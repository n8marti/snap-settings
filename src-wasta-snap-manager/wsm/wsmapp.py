""" Main GUI module. """

import gi
import os
import subprocess

from pathlib import Path
current_file_path = Path(os.path.abspath(__file__))

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from wsm import handler
from wsm import setupui
from wsm import util
from wsm import snapd


class WSMApp():
    def __init__(self):
        # Get UI location based on current file location.
        ui_dir = '/usr/share/wasta-snap-manager'
        if current_file_path.parents[1].parts[-1][0:3] == 'src':
            ui_dir = str(current_file_path.parents[1] / 'ui')

        # Define app-wide variables.
        self.installed_snaps_list = snapd.snap.list()
        self.installable_snaps_list = []
        self.updatable_offline_list = []
        self.updatable_online_list = []

        # Get widgets from glade file.
        self.builder = Gtk.Builder()
        self.builder.add_from_file(ui_dir + '/snap-manager.glade')
        self.grid_source = self.builder.get_object('grid_source')
        self.button_source_online = self.builder.get_object('button_source_online')
        self.label_button_source_online = self.builder.get_object('label_button_source_online')
        self.button_source_offline = self.builder.get_object('button_source_offline')
        self.window_installed_snaps = self.builder.get_object("scrolled_window_installed")
        self.window_available_snaps = self.builder.get_object("scrolled_window_available")
        self.window = self.builder.get_object('window_snap_manager')

        # Make GUI initial adjustments.
        self.user, self.start_folder = setupui.guess_offline_source_folder()
        self.button_source_offline.set_current_folder(self.start_folder)

        # Add runtime widgets.
        self.listbox_installed = Gtk.ListBox()
        self.listbox_installed.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.listbox_installed.set_activate_on_single_click(True)
        self.listbox_available = Gtk.ListBox()
        self.listbox_available.set_selection_mode(Gtk.SelectionMode.NONE)

        # Create viewports for Installed & Available panes.
        self.wis_vp = Gtk.Viewport()
        self.wis_vp.add_child(self.builder, self.listbox_installed)
        self.window_installed_snaps.add_child(self.builder, self.wis_vp)
        self.rows = setupui.populate_listbox_installed(self.listbox_installed, self.installed_snaps_list)
        self.was_vp = Gtk.Viewport()
        self.was_vp.add_child(self.builder, self.listbox_available)
        self.window_available_snaps.add_child(self.builder, self.was_vp)
        self.window_installed_snaps.show()
        #self.window_available_snaps.show()
        self.wis_vp.show()

        # List populated later with self.populate_listbox_available().
        #   But initial entry added here for user guidance.
        self.av_row_init = Gtk.ListBoxRow()
        self.listbox_available.add(self.av_row_init)
        text = "<span style=\"italic\">Please select an offline folder above.</span>"
        self.label_av_row_init = Gtk.Label(text)
        self.label_av_row_init.set_property("use-markup", True)
        self.av_row_init.add(self.label_av_row_init)
        # I can't get this to show up, so doing it manually instead.
        #self.listbox_available.set_placeholder(self.av_row_init)
        self.was_vp.show_all()

        # Connect GUI signals to Handler class.
        self.builder.connect_signals(handler.h)

    def select_offline_update_rows(self, source_folder, init=False):
        rows = self.rows
        # Determine if it's a wasta-offline folder.
        basename = Path(source_folder).name
        if init and basename != 'wasta-offline':
            # Intial run and no 'wasta-offline' folder found. Return empty dictionary.
            offline_dict = {}
            return offline_dict
        #offline_snaps = util.list_offline_snaps(source_folder)
        updatable_offline = self.updatable_offline_list
        #updatable_offline = []
        if len(updatable_offline) > 0:
            #updatable = util.get_offline_updatable_snaps(self.installed_snaps_list, offline_snaps)
            for entry in updatable_offline:
                #updatable_offline.append(entry['name'])
                index = rows[entry['name']]
                row = self.listbox_installed.get_row_at_index(index)
                self.listbox_installed.select_row(row)
        return updatable_offline

    def select_online_update_rows(self):
        installed_snaps = self.installed_snaps_list
        rows = self.rows
        #if len(self.updatable_online_list) == 0:
        #    self.updatable_online_list = util.get_snap_refresh_list()
        for snap in self.updatable_online_list:
            index = rows[snap]
            row = self.listbox_installed.get_row_at_index(index)
            self.listbox_installed.select_row(row)
            box_row = row.get_child()
            #row.label_update_note.show()

    def deselect_online_update_rows(self):
        installed_snaps = self.installed_snaps_list
        rows = self.rows
        #if len(self.updatable_online_list) == 0:
        #    self.updatable_online_list = util.get_snap_refresh_list()
        for snap in self.updatable_online_list:
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
            install_button.connect("clicked", handler.h.on_install_button_clicked, snap)
            rows[snap] = index
            index += 1
            row.show_all()
        list_box.show()
        return rows


app = WSMApp()

# Adjust GUI in case of found 'wasta-offline' folder.
app.updatable_offline_list = util.get_offline_updatable_snaps(app.start_folder)
if len(app.updatable_offline_list) > 0:
    app.select_offline_update_rows(app.start_folder, init=True)
app.installable_snaps_list = util.get_offline_installable_snaps(app.start_folder)
if len(app.installable_snaps_list) > 0:
    app.populate_listbox_available(app.listbox_available, app.installable_snaps_list)
