# Imported by wasta-snap-manager executable.

import gi
import os
import subprocess

from pathlib import Path
current_file_path = Path(os.path.abspath(__file__))

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import wsm.setupui
import wsm.snapctl


class Handler:
    def gtk_widget_destroy(self, *args):
        Gtk.main_quit()

    def on_button_settings_clicked(*args):
        try:
            subprocess.run(['pkexec', '/usr/bin/snap-settings'])
        except:
            # Snap Settings app not found?
            print("Some error occurred!")

    def on_button_source_online_toggled(self, *args):
        # Send any useful output to adjacent label field.
        test_source_online = args[0].get_active()
        global app
        text = ''
        if test_source_online:
            if wsm.snapctl.snap_store_accessible():
                app.select_online_update_rows()
                response = True
            else:
                text = 'No connection to the Snap Store.'
                app.button_source_online.set_active(False)
                response = False
        else:
            text = ''
            app.deselect_online_update_rows()
            response = False

        app.label_button_source_online.set_text(text)
        return response

    def on_button_source_offline_file_set(self, folder_obj):
        folder = folder_obj.get_filename()
        # Look for wasta-offline folder as starting point.
        # Verify appropriateness of selected folder.
        # Include this offline folder in update sources list.
        global app
        rows = app.rows
        installed = app.installed_snaps
        app.select_offline_update_rows(folder)

    def on_button_update_snaps_clicked(self, *args):
        # Can't pass listbox contents from Glade because it doesn't exist yet,
        #   so the listbox has to be grabbed from the instantiated WSMApp.
        global app
        obj_rows_selected = app.listbox_installed.get_selected_rows()
        update_list = []
        for obj in obj_rows_selected:
            # child = box; children = icon, box_info, label_update_note
            box_children = obj.get_child().get_children()
            # children = snap_name, description
            snap_name = box_children[1].get_children()[0].get_text()
            update_list.append(snap_name)
            label_update_note = box_children[2].get_text()
        print(update_list)

    def on_button_remove_snaps_clicked(*args):
        # TODO: Doesn't work when app runs with pkexec!
        try:
            proc = subprocess.run(
                ['/snap/bin/snap-store', '--mode=installed'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except:
            # Snap Store not installed?
            print(subprocess.stdout, subprocess.stderr)

class WSMApp():
    def installed_on_system(self, installed):
        installed_on_system = installed
        return installed

    def select_offline_update_rows(self, source_folder, init=False):
        installed_snaps = self.installed_snaps
        rows = self.rows
        # Determine if it's a wasta-offline folder.
        basename = Path(source_folder).name
        if init and basename != 'wasta-offline':
            # Intial run and no 'wasta-offline' folder found. Return empty dictionary.
            offline_dict = {}
            return offline_dict
        offline_snaps = wsm.snapctl.list_offline_snaps(source_folder)
        if len(offline_snaps) > 0:
            updatable = wsm.snapctl.get_offline_updatable_snaps(installed_snaps, offline_snaps)
            for snap in updatable:
                index = rows[snap]
                row = self.listbox_installed.get_row_at_index(index)
                self.listbox_installed.select_row(row)

    def select_online_update_rows(self):
        installed_snaps = self.installed_snaps
        rows = self.rows
        global updatable_online
        if len(updatable_online) == 0:
            updatable_online = wsm.snapctl.api_get_snap_refresh()
        for snap in updatable_online:
            index = rows[snap]
            row = self.listbox_installed.get_row_at_index(index)
            self.listbox_installed.select_row(row)

    def deselect_online_update_rows(self):
        installed_snaps = self.installed_snaps
        rows = self.rows
        global updatable_online
        if len(updatable_online) == 0:
            updatable_online = wsm.snapctl.api_get_snap_refresh()
        for snap in updatable_online:
            index = rows[snap]
            row = self.listbox_installed.get_row_at_index(index)
            self.listbox_installed.unselect_row(row)

    # Get UI location based on current file location.
    ui_dir = '/usr/share/wasta-snap-manager'
    if current_file_path.parents[1].parts[-1][0:3] == 'src':
        ui_dir = str(current_file_path.parents[1] / 'ui')

    # Get widgets from glade file.
    builder = Gtk.Builder()
    builder.add_from_file(ui_dir + '/snap-manager.glade')
    button_source_online = builder.get_object('button_source_online')
    label_button_source_online = builder.get_object('label_button_source_online')
    button_source_offline = builder.get_object('button_source_offline')
    window_installed_snaps = builder.get_object("scrolled_window_installed")
    window = builder.get_object('window_snap_manager')

    # Add runtime widgets.
    listbox_installed = Gtk.ListBox()
    listbox_installed.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
    listbox_installed.set_activate_on_single_click(True)

    # Make GUI initial adjustments.
    start_folder = wsm.setupui.guess_offline_source_folder()
    button_source_offline.set_current_folder(start_folder)

    wis_vp = Gtk.Viewport()
    wis_vp.add_child(builder, listbox_installed)
    window_installed_snaps.add_child(builder, wis_vp)

    installed_snaps = wsm.snapctl.api_get_snap_list()
    rows = wsm.setupui.populate_listbox(listbox_installed, installed_snaps)

    # Connect GUI signals to Handler class.
    builder.connect_signals(Handler())


app = WSMApp()
# Adjust GUI in case of found 'wasta-offline' folder.
app.select_offline_update_rows(app.start_folder, init=True)
updatable_online = wsm.snapctl.api_get_snap_refresh()
