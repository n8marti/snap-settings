# Utility functions module.

import platform
import subprocess
import urllib.request

from pathlib import Path

from wsm import wsmapp
from wsm.snapd import snap


def get_snap_refresh_list():
    updatable = [s['name'] for s in snap.refresh_list()]
    return updatable

def add_item_to_update_list(*args):
    # Convert list to 'set' type to eliminate duplicates.
    item_to_add = args[0]
    update_set = set(args[1])
    update_set.add(item_to_add)
    # Convert back to list before returning.
    update_list = list(update_set)
    return update_list

def get_list_from_snaps_folder(dir):
    list = []
    for assertfile in Path(dir).glob('*.assert'):
        # Each assert file is found first, then the corresponding snap file.
        snapfile = str(Path(dir, assertfile.stem + '.snap'))
        if Path(snapfile).exists():
            # The snap file is only included if both the assert and snap exist.
            snap, rev = Path(snapfile).stem.split('_')
            dictionary = {'name': snap, 'revision': rev, 'file_path': snapfile}
            list.append(dictionary)
    return list

def list_offline_snaps(dir, init=False):
    # Called at 2 different times:
    #   1. 'wasta-offline' found automatically; i.e. init=True
    #   2. User selects an arbitrary folder; i.e. init=False

    # Get basename of given dir.
    basename = Path(dir).name
    offline_list = []

    # Determine if it's a wasta-offline folder.
    if init and basename != 'wasta-offline':
        # Initial folder is user's home folder.
        return offline_list

    # Get arch in order to search correct wasta-offline folders.
    arch = platform.machine()
    if arch != 'x86_64':
        print("Arch", arch, "not supported yet for offline updates.")
        return offline_list
    else:
        arch = 'amd64'

    # Search the given directory for snaps.
    folders = ['.', 'all', arch]
    for folder in folders:
        if basename != 'wasta-offline':
            # An arbitrary folder is selected by the user.
            folder_path = Path(dir, folder)
        else:
            # A 'wasta-offline' folder is being used.
            folder_path = Path(dir, 'local-cache', 'snaps', folder)
        if folder_path.exists():
            # Add new dictionary from folder to existing one.
            #offline_dict.update(get_dict_from_snaps_folder(folder_path))
            #print(folder_path)
            offline_list += get_list_from_snaps_folder(folder_path)
    return offline_list

def get_offline_updatable_snaps(installed_snaps_list, offline_snaps_list):
    updatable_snaps_list = []
    for inst in installed_snaps_list:
        for offl in offline_snaps_list:
            if offl['name'] == inst['name'] and offl['revision'] > inst['revision']:
                updatable_snaps_list.append(offl)
    return updatable_snaps_list

def get_offline_updates(available):
    # Both 'available' and 'installed' are dictionaries, {'snap': 'rev'}.
    installed = get_installed_snaps()
    global update_dict
    for snap, details in installed.items():
        rev_installed = details[0]
        if snap in available.keys():
            rev_available = available[snap]
            if rev_available > rev_installed:
                update_list = add_item_to_update_list(snap, update_list)
    return update_dict

def update_snap_online(snap):
    print('$ pkexec snap refresh', snap)
    return
    try:
        subprocess.run(['pkexec', 'snap', 'refresh', snap])
    except:
        print("Error during snap refresh.")
        return 13

def install_snap_offline(snap_file_path):
    print('$ snap install', snap_file_path, '...')
    return
    #base, ext = os.path.splitext(snap_file_path)
    snap_file = Path(snap_file_path)
    base = snap_file.stem
    ext = snap_file.suffix
    assert_file_path = base + '.assert'
    assert_file = Path(assert_file_path)
    if not assert_file.is_file() or not snap_file.is_file():
        return 10
    try:
        subprocess.run(['pkexec', 'snap', 'ack', assert_file_path])
    except:
        print("Assert file not accepted.")
        return 11
    try:
        subprocess.run(['pkexec', 'snap', 'install', snap_file_path])
    except:
        # What are the possible errors here?
        print("Error during snap install from ", snap_file_path)
        return 12

def snap_store_accessible():
    try:
        urllib.request.urlopen('https://api.snapcraft.io', data=None, timeout=3)
        return True
    except urllib.error.URLError:
        return False
