""" Utility functions module. """

import os
import platform
import re
import subprocess
import tempfile
import urllib.request

from pathlib import Path

from wsm import wsmapp
from wsm.snapd import snap


def get_snap_refresh_list():
    updatable = [s['name'] for s in snap.refresh_list()]
    return updatable

def add_item_to_update_list(item, update_list):
    # Convert list to 'set' type to eliminate duplicates.
    update_set = set(update_list)
    update_set.add(item)
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

def get_offline_installable_snaps(snaps_folder):
    # Include this offline folder in update sources list.
    rows = wsmapp.app.rows
    installed_snaps_list = wsmapp.app.installed_snaps
    wsmapp.app.updatable_offline = wsmapp.app.select_offline_update_rows(snaps_folder)
    offline_snaps_list = list_offline_snaps(snaps_folder)
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
    return wsmapp.app.installable_snaps_list

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

def snap_store_accessible():
    try:
        urllib.request.urlopen('https://api.snapcraft.io', data=None, timeout=3)
        return True
    except urllib.error.URLError:
        return False

def cat_yaml(snapfile):
    # Data needed: 'base', 'confinement', 'prerequisites'
    yaml = 'meta/snap.yaml'
    DEVNULL = open(os.devnull, 'w')
    with tempfile.TemporaryDirectory() as dest:
        subprocess.run(
            ['unsquashfs', '-n',  '-force', '-dest', dest, snapfile, '/' + yaml],
            stdout=DEVNULL
        )
        with open(Path(dest, yaml)) as file:
            return file.read()

def get_offline_snap_details(snapfile):
    contents = cat_yaml(snapfile).splitlines()
    p = Path(snapfile)
    name, revision = p.stem.split('_')
    output_dict = {'name': name}
    output_dict['revision'] = revision
    output_dict['base'] = 'core' # overwritten if 'base' specified in yaml
    for line in contents:
        if re.match('.*base\:.*', line):
            output_dict['base'] = line.split(':')[1].strip()
        elif re.match('.*confinement\:.*', line):
            output_dict['confinement'] = line.split(':')[1].strip()
        elif re.match('.*default\-provider\:.*', line):
            # TODO: It might be possible to have > 1 default-providers!
            output_dict['prerequisites'] = line.split(':')[1].strip()
        else:
            continue
    return output_dict

def snap_is_installed(snap_name):
    response = snap.info(snap_name)
    try:
        if response['name'] == snap_name:
            return True
        else: # maybe not possible?
            return False
    except KeyError:
        return False
