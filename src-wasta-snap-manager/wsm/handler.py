### UNUSED ###

# Signal handler

import gi
import subprocess

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import snapctl


class Handler:
    def gtk_widget_destroy(self, *args):
        Gtk.main_quit()

    def on_button_settings_clicked(*args):
        try:
            subprocess.run(['pkexec', '/usr/bin/snap-settings'])
        except:
            # Snap Settings app not found?
            print("Some error occurred!")

    def on_button_source_online_toggled(*args):
        # Send any useful output to adjacent label field.
        test_source_online = args[1].get_active()
        #global app
        text = ''
        if test_source_online:
            if snapctl.snap_store_accessible():
                response = True
            else:
                text = 'No connection to the Snap Store.'
                app.button_source_online.set_active(False)
                response = False
        else:
            text = ''
            response = False

        app.label_button_source_online.set_text(text)
        return response

    def on_button_source_offline_file_set(*args):
        # Look for wasta-offline folder as starting point.
        # Verify appropriateness of selected folder.
        # Set full folder path as adjacent label text.
        # Include this offline folder in update sources list.
        print(args[1].get_text())

    def on_button_update_snaps_clicked(*args):
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
        try:
            subprocess.run(['snap-store', '--mode=installed'])
        except:
            # Snap Store not installed?
            print("Some error occurred!")
