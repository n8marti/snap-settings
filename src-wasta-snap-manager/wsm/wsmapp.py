# Imported by wasta-snap-manager executable.

import gi
import os
import subprocess

from pathlib import Path
current_file_path = Path(os.path.abspath(__file__))

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from wsm import handler
from wsm import setupui
from wsm import snapctl
from wsm import snapd


class WSMApp():
    def select_offline_update_rows(self, source_folder, init=False):
        rows = self.rows
        # Determine if it's a wasta-offline folder.
        basename = Path(source_folder).name
        if init and basename != 'wasta-offline':
            # Intial run and no 'wasta-offline' folder found. Return empty dictionary.
            offline_dict = {}
            return offline_dict
        offline_snaps = snapctl.list_offline_snaps(source_folder)
        updatable_offline = []
        if len(offline_snaps) > 0:
            updatable = snapctl.get_offline_updatable_snaps(self.installed_snaps, offline_snaps)
            for entry in updatable:
                updatable_offline.append(entry['name'])
                index = rows[entry['name']]
                row = self.listbox_installed.get_row_at_index(index)
                self.listbox_installed.select_row(row)
        return updatable_offline

    def select_online_update_rows(self):
        installed_snaps = self.installed_snaps
        rows = self.rows
        #global updatable_online
        if len(self.updatable_online) == 0:
            updatable_online = snapctl.get_snap_refresh_list()
        for snap in self.updatable_online:
            index = rows[snap]
            row = self.listbox_installed.get_row_at_index(index)
            self.listbox_installed.select_row(row)

    def deselect_online_update_rows(self):
        installed_snaps = self.installed_snaps
        rows = self.rows
        #global updatable_online
        if len(self.updatable_online) == 0:
            self.updatable_online = snapctl.get_snap_refresh_list()
        for snap in self.updatable_online:
            index = rows[snap]
            row = self.listbox_installed.get_row_at_index(index)
            self.listbox_installed.unselect_row(row)

    def populate_listbox_available(self, list_box, snaps_list):
        # Create dictionary of relevant info.
        contents_list = []
        for entry in snaps_list:
            contents_list.append(entry['name'])
        rows = {}
        index = 0
        for snap in sorted(contents_list):
            row = setupui.AvailableSnapRow(snap)
            list_box.add(row)
            install_button = row.button_install_offline
            install_button.connect("clicked", handler.Handler.on_install_button_clicked, snap)
            rows[snap] = index
            index += 1
        list_box.show_all()
        return rows

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
    window_available_snaps = builder.get_object("scrolled_window_available")
    window = builder.get_object('window_snap_manager')

    # Make GUI initial adjustments.
    user, start_folder = setupui.guess_offline_source_folder()
    button_source_offline.set_current_folder(start_folder)

    # Add runtime widgets.
    listbox_installed = Gtk.ListBox()
    listbox_installed.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
    listbox_installed.set_activate_on_single_click(True)
    listbox_available = Gtk.ListBox()
    listbox_available.set_selection_mode(Gtk.SelectionMode.NONE)

    # Create viewports for Install & Available panes.
    wis_vp = Gtk.Viewport()
    wis_vp.add_child(builder, listbox_installed)
    window_installed_snaps.add_child(builder, wis_vp)
    #installed_snaps = snapctl.api_get_snap_list()
    installed_snaps = snapd.snap.list()
    rows = setupui.populate_listbox_installed(listbox_installed, installed_snaps)
    was_vp = Gtk.Viewport()
    was_vp.add_child(builder, listbox_available)
    window_available_snaps.add_child(builder, was_vp)
    # List populated later with self.populate_listbox_available().

    # Connect GUI signals to Handler class.
    builder.connect_signals(handler.Handler())


app = WSMApp()
# Adjust GUI in case of found 'wasta-offline' folder.
app.updatable_offline = app.select_offline_update_rows(app.start_folder, init=True)
app.updatable_online = snapctl.get_snap_refresh_list()
