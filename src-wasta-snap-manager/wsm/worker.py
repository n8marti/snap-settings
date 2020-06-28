# All of these functions run inside of threads and use GLib to communicate back.

from gi.repository import GLib

from wsm import handler
from wsm import snapctl
from wsm import wsmapp


def handle_button_online_source_toggled(button):
    is_activated = button.get_active()
    text = ''
    # Clear the label text if not empty.
    GLib.idle_add(wsmapp.app.label_button_source_online.set_text, text)
    if is_activated:
        text = 'Checking the Snap Store...'
        GLib.idle_add(wsmapp.app.label_button_source_online.set_text, text)
        if snapctl.snap_store_accessible():
            text = ''
            wsmapp.app.select_online_update_rows()
        else:
            text = 'No connection to the Snap Store.'
            wsmapp.app.button_source_online.set_active(False)
    else:
        text = ''
        wsmapp.app.deselect_online_update_rows()

    GLib.idle_add(wsmapp.app.label_button_source_online.set_text, text)
    return

def handle_button_update_snaps_clicked():
    # Make sure on_button_source_online_toggled has finished before continuing.
    handler.h.t_online_check.join()
    obj_rows_selected = wsmapp.app.listbox_installed.get_selected_rows()
    update_list = []
    for obj in obj_rows_selected:
        # child = box; children = icon, box_info, label_update_note
        box_children = obj.get_child().get_children()
        # children = snap_name, description
        snap_name = box_children[1].get_children()[0].get_text()
        update_list.append(snap_name)
        label_update_note = box_children[2].get_text()
    details_l = wsmapp.app.installable_snaps_list
    for snap in update_list:
        # Update from offline source first.
        file_paths = [entry['file_path'] for entry in details_l if entry['name'] == snap]
        if snap in wsmapp.app.updatable_offline:
            snapctl.install_snap_offline(file_paths[0])
        # Update from online source.
        if snap in wsmapp.app.updatable_online:
            snapctl.update_snap_online(snap)
    # TODO:
    #   - show progress spinner for each snap?
    #   - re-populate selection list to remove updated snaps

def handle_install_button_clicked(button, snap):
    list = wsmapp.app.installable_snaps_list
    # Use list comprehension to get "list" of the single matching item.
    file_paths = [entry['file_path'] for entry in list if entry['name'] == snap]
    # Install snap using "1st" item in "list".
    snapctl.install_snap_offline(file_paths[0])
    # During install:
    #   - replace button with progress spinner
    # After installation complete:
    #   - re-calculate installed_list
    #   - make row "grayed out"
    #   - remove install_button
