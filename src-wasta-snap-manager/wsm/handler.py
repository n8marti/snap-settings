# Signal handler module.

#import concurrent.futures
import gi
import subprocess
import threading

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from wsm import util
from wsm import worker
from wsm import wsmapp


class Handler():
    def gtk_widget_destroy(self, *args):
        Gtk.main_quit()

    def on_button_settings_clicked(self, *args):
        try:
            subprocess.run(['pkexec', '/usr/bin/snap-settings'])
        except:
            # Snap Settings app not found?
            print("Some error occurred!")

    def on_button_source_online_toggled(self, button):
        target = worker.handle_button_online_source_toggled
        self.t_online_check = threading.Thread(target=target, args=(button,))
        self.t_online_check.start()

    def on_button_source_offline_file_set(self, folder_obj):
        folder = folder_obj.get_filename()
        # Include this offline folder in update sources list.
        rows = wsmapp.app.rows
        installed_snaps_list = wsmapp.app.installed_snaps
        wsmapp.app.updatable_offline = wsmapp.app.select_offline_update_rows(folder)
        offline_snaps_list = util.list_offline_snaps(folder)
        copy = offline_snaps_list
        # Remove older revisions of each snap from list.
        for entry in offline_snaps_list:
            for e in copy:
                if entry['name'] == e['name'] and int(entry['revision']) < int(e['revision']):
                    offline_snaps_list.remove(entry)
        # Make list of installable snaps (offline snaps minus installed snaps).
        wsmapp.app.installable_snaps_list.extend(offline_snaps_list)
        for offl in offline_snaps_list:
            for inst in installed_snaps_list:
                if offl['name'] == inst['name']:
                    wsmapp.app.installable_snaps_list.remove(offl)
        # Remove placeholder row, then populate available snaps rows.
        wsmapp.app.listbox_available.remove(wsmapp.app.av_row_init)
        wsmapp.app.rows1 = wsmapp.app.populate_listbox_available(wsmapp.app.listbox_available, wsmapp.app.installable_snaps_list)

    def on_button_update_snaps_clicked(self, *args):
        target = worker.handle_button_update_snaps_clicked
        self.t_update_snaps = threading.Thread(target=target)
        self.t_update_snaps.start()

    def on_button_remove_snaps_clicked(self, *args):
        # TODO: Doesn't work when app runs with pkexec!
        #   Even in terminal, and even with an annotation entry added in polkit,
        #   and even with pkexec --user nate, it fails with a segmentation fault.
        #   Likewise if using sudo --user=nate ...
        try:
            proc = subprocess.run(
                ['/snap/bin/snap-store', '--mode=installed'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except:
            # Snap Store not installed?
            print(subprocess.stdout, subprocess.stderr)

    def on_install_button_clicked(self, button, snap):
        target = worker.handle_install_button_clicked
        self.t_install_snap = threading.Thread(target=target, args=(button, snap))
        self.t_install_snap.start()


h = Handler()
