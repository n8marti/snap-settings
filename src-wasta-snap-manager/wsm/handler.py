# Signal handler

import gi
import subprocess

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from wsm import wsmapp
from wsm import snapctl


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
        text = ''
        if test_source_online:
            if snapctl.snap_store_accessible():
                wsmapp.app.select_online_update_rows()
                response = True
            else:
                text = 'No connection to the Snap Store.'
                wsmapp.app.button_source_online.set_active(False)
                response = False
        else:
            text = ''
            wsmapp.app.deselect_online_update_rows()
            response = False

        wsmapp.app.label_button_source_online.set_text(text)
        return response

    def on_button_source_offline_file_set(self, folder_obj):
        folder = folder_obj.get_filename()
        # Include this offline folder in update sources list.
        rows = wsmapp.app.rows
        installed_snaps_list = wsmapp.app.installed_snaps
        wsmapp.app.select_offline_update_rows(folder)
        offline_snaps_list = snapctl.list_offline_snaps(folder)
        installable_snaps_list = offline_snaps_list
        for offl in offline_snaps_list:
            for inst in installed_snaps_list:
                if offl['name'] == inst['name']:
                    installable_snaps_list.remove(offl)
        wsmapp.app.rows1 = wsmapp.app.populate_listbox_available(wsmapp.app.listbox_available, installable_snaps_list)

    def on_button_update_snaps_clicked(self, *args):
        # Can't pass listbox contents from Glade because it doesn't exist yet,
        #   so the listbox has to be grabbed from the instantiated WSMApp.
        obj_rows_selected = wsmapp.app.listbox_installed.get_selected_rows()
        update_list = []
        for obj in obj_rows_selected:
            # child = box; children = icon, box_info, label_update_note
            box_children = obj.get_child().get_children()
            # children = snap_name, description
            snap_name = box_children[1].get_children()[0].get_text()
            update_list.append(snap_name)
            label_update_note = box_children[2].get_text()
        print(update_list)
        # TODO:
        #   - update offline snaps: $ snap ack/install [snap_file]?
        #   - update online snaps $ snap refresh [snap]?
        #   - show progress spinner for each snap?
        #   - re-populate selection list to remove updated snaps

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

    def on_install_button_clicked(self, snap):
        # Install snap.
        print('[ $ snap install', snap, ']')
        snap_file = '[unknown]'
        snapctl.install_snap(snap_file)
        # During install:
        #   - replace button with progress spinner
        # After installation complete:
        #   - re-calculate installed_list
        #   - make row "grayed out"
        #   - remove install_button
