# All of these functions run inside of threads and use GLib to communicate back.

import gi
from gi.repository import Gtk, GLib
gi.require_version("Gtk", "3.0")

from wsm import handler
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
    details_l = wsmapp.app.installable_snaps_list
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

        # Update from offline source first.
        file_paths = [entry['file_path'] for entry in details_l if entry['name'] == snap_name]
        label_update_note.hide()
        spinner.show()
        spinner.start()
        from time import sleep
        for s in range(3):
            sleep(1)
        if snap_name in wsmapp.app.updatable_offline:
            util.install_snap_offline(file_paths[0])
        # Update from online source.
        if snap_name in wsmapp.app.updatable_online:
            util.update_snap_online(snap_name)

        # Post-install.
        spinner.stop()
        spinner.hide()
        # if install successful:
        listbox.unselect_row(row)
        #row.hide()

def handle_install_button_clicked(button, snap):
    list = wsmapp.app.installable_snaps_list
    # Use list comprehension to get "list" of the single matching item.
    file_paths = [entry['file_path'] for entry in list if entry['name'] == snap]
    # Install snap using "1st" item in "list".
    width = button.get_allocated_width()
    box_row = button.get_parent()
    spinner = Gtk.Spinner(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
    spinner.set_property("width-request", width)
    box_row.pack_end(spinner, False, True, 5)
    button.hide()
    spinner.show()
    spinner.start()
    from time import sleep
    for s in range(8):
        sleep(1)
    # Install snap.
    util.install_snap_offline(file_paths[0])
    # Post-install.
    spinner.stop()
    spinner.hide()
    # if install successful:
    box_row.hide()
    # else:
        # button.show()
