""" Functions that run in background threads. """
# All of these functions run inside of threads and use GLib to communicate back.

import gi
import subprocess

from pathlib import Path
from gi.repository import Gtk, GLib
gi.require_version("Gtk", "3.0")

from wsm import handler
from wsm import setupui
from wsm import snapd
from wsm import util
from wsm import wsmapp


def handle_button_online_source_toggled(button):
    is_activated = button.get_active()

    label = wsmapp.app.label_button_source_online
    grid = wsmapp.app.grid_source
    spinner = Gtk.Spinner(halign=Gtk.Align.START)

    text = ''
    # Clear the label text if not empty.
    GLib.idle_add(label.set_text, text)
    if is_activated:
        #text = 'Checking the Snap Store...'
        #GLib.idle_add(wsmapp.app.label_button_source_online.set_text, text)
        GLib.idle_add(label.hide)
        GLib.idle_add(grid.attach, spinner, 2, 0, 1, 1)
        GLib.idle_add(spinner.show)
        GLib.idle_add(spinner.start)
        if util.snap_store_accessible():
            text = ''
            wsmapp.app.updatable_online_list = util.get_snap_refresh_list()
            wsmapp.app.select_online_update_rows()
        else:
            text = 'No connection to the Snap Store.'
            wsmapp.app.button_source_online.set_active(False)
        GLib.idle_add(spinner.stop)
        GLib.idle_add(spinner.hide)
        GLib.idle_add(label.show)
    else:
        text = ''
        wsmapp.app.deselect_online_update_rows()

    GLib.idle_add(label.set_text, text)
    return

def handle_button_update_snaps_clicked():
    # Make sure on_button_source_online_toggled has finished before continuing.
    handler.h.t_online_check.join()
    obj_rows_selected = wsmapp.app.listbox_installed.get_selected_rows()
    #list = wsmapp.app.installable_snaps_list
    list = wsmapp.app.updatable_offline_list
    offline_names = [i['name'] for i in wsmapp.app.updatable_offline_list]
    for row in obj_rows_selected:
        listbox = row.get_parent()
        # child = box; children = icon, box_info, label_update_note
        box_row = row.get_child()
        box_children = box_row.get_children()
        label_update_note = box_children[2]
        # children = snap_name, description
        snap_name = box_children[1].get_children()[0].get_text()
        label_update_text = label_update_note.get_text()

        spinner = Gtk.Spinner(halign=Gtk.Align.START, valign=Gtk.Align.CENTER)
        box_row.pack_end(spinner, False, False, 5)
        label_update_note.hide()
        spinner.show()
        spinner.start()

        # Update from offline source first.
        if snap_name in offline_names:
            file_paths = [i['file_path'] for i in list if i['name'] == snap_name]
            file_path = Path(file_paths[0])

            offline_snap_details = (util.get_offline_snap_details(file_path))
            classic_flag=False
            try:
                confinement = offline_snap_details['confinement']
                if confinement == 'classic':
                    classic_flag=True
            except KeyError:
                pass

            install_snap_offline(file_path, classic_flag)

        # Update from online source.
        if snap_name in wsmapp.app.updatable_online_list:
            update_snap_online(snap_name)

        # Post-install.
        spinner.stop()
        spinner.hide()
        # if install successful:
        listbox.unselect_row(row)
        #row.hide()

def handle_install_button_clicked(button, snap):
    # Adjust GUI items.
    width = button.get_allocated_width()
    box_row = button.get_parent()
    row = box_row.get_parent()
    spinner = Gtk.Spinner(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
    spinner.set_property("width-request", width)
    box_row.pack_end(spinner, False, True, 5)
    button.hide()
    spinner.show()
    spinner.start()

    # Get snap and assert files.
    list = wsmapp.app.installable_snaps_list
    # Use list comprehension to get "list" of the single matching item.
    file_paths = [i['file_path'] for i in list if i['name'] == snap]
    file_path = Path(file_paths[0])

    # Read /meta/snap.yaml in snap file to get 'core' and 'prerequisites'.
    # TODO: This only returns 1 preprequisite; i.e. "default-provider: <prerequisite>"
    offline_snap_details = (util.get_offline_snap_details(file_path))

    classic_flag=False
    try:
        confinement = offline_snap_details['confinement']
        if confinement == 'classic':
            classic_flag=True
    except KeyError:
        pass

    # Install 'core' and 'prerequisites', if necessary.
    ret = 0 # initialize return code list
    try:
        base = offline_snap_details['base']
    except KeyError: # this should never happen
        base = 'core'
    if not util.snap_is_installed(base):
        base_paths = [entry['file_path'] for entry in list if entry['name'] == base]
        base_path = Path(base_paths[0])
        ret += install_snap_offline(base_path, classic_flag)
        if ret == 0:
            # TODO: Remove base from available list.
            # Re-populate installed snaps window.
            listbox = wsmapp.app.listbox_installed
            setupui.populate_listbox_installed(listbox, snapd.snap.list())
    try:
        prereq = offline_snap_details['prerequisites']
        if not util.snap_is_installed(prereq):
            prereq_paths = [entry['file_path'] for entry in list if entry['name'] == prereq]
            prereq_path = Path(prereq_paths[0])
            ret += install_snap_offline(prereq_path, classic_flag)
            if ret == 0:
                # TODO: if successful, remove prereq from available list.
                # Re-populate installed snaps window.
                listbox = wsmapp.app.listbox_installed
                setupui.populate_listbox_installed(listbox, snapd.snap.list())
    except KeyError: # no prerequisites
        pass

    # Install offline snap itself.
    ret += install_snap_offline(file_path, classic_flag)
    if ret == 0:
        # Re-populate installed snaps window.
        listbox = wsmapp.app.listbox_installed
        setupui.populate_listbox_installed(listbox, snapd.snap.list())

    # Post-install.
    spinner.stop()
    spinner.hide()
    if ret == 0: # successful installation
        row.hide()
    else: # failed installation
        button.show()

def update_snap_online(snap):
    #print('$ pkexec snap refresh', snap)
    try:
        subprocess.run(['pkexec', 'snap', 'refresh', snap])
        return 0
    except Exception as e:
        print("Error during snap refresh:")
        print(e)
        return 13

def install_snap_offline(snap_file, classic_flag):
    dir = snap_file.parent
    base = snap_file.stem
    name = base.split('_')[0]
    ext = snap_file.suffix
    assert_file_name = base + '.assert'
    assert_file = Path(dir, assert_file_name)

    if not assert_file.is_file() or not snap_file.is_file():
        print('Snap', name, 'not available for offline installation.')
        print('Try installing', name, 'from the Snap Store instead.')
        # TODO: Display message saying how to install it from the Snap Store.
        return 10
    try:
        subprocess.run(
            ['pkexec', 'snap', 'ack', assert_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    except Exception as e:
        print("Assert file not accepted:")
        print(e)
        return 11
    try:
        if classic_flag:
            subprocess.run(['pkexec', 'snap', 'install', '--classic', snap_file])
            return 0
        else:
            subprocess.run(['pkexec', 'snap', 'install', snap_file])
            return 0
    except Exception as e:
        # What are the possible errors here?
        print("Error during snap install from ", snap_file + ':')
        print(e)
        return 12
