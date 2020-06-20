# Snapd-related functions.

import os
import platform
import requests
import subprocess
import urllib.request

from pathlib import Path

import wsm.snapdrequests

"""
def get_installed_snaps():
    installed_snaps = {}
    # Get output from: $ snap list
    snap_list = subprocess.run(
        ['snap', 'list'],
        stdout=subprocess.PIPE
    )
    installed_snaps = parse_snap_list(snap_list.stdout)
    return installed_snaps
"""

def api_get_snap_list():
    payload = '/v2/snaps'
    session = requests.Session()
    fake_http = "http://snapd/"
    session.mount(fake_http, wsm.snapdrequests.SnapdAdapter())
    result = session.get(fake_http + payload).json()['result'] # list of snap dicts
    snaps_list_dict = {}
    for s in result:
        try:
            icon = s['icon']
        except KeyError:
            icon = '/usr/share/icons/gnome/scalable/places/poi-marker.svg'
        #icon = '[none]'
        #snaps_list_dict[s['name']] = [s['revision'], s['confinement'], s['summary']]
        snaps_list_dict[s['name']] = {
            'name': s['name'],
            'icon': icon,
            'summary': s['summary'],
            'revision': s['revision'],
            'confinement': s['confinement']
        }
    return snaps_list_dict

def api_get_snap_info(snap):
    payload = '/v2/snaps/' + snap
    session = requests.Session()
    fake_http = "http://snapd/"
    session.mount(fake_http, wsm.snapdrequests.SnapdAdapter())
    info_dict = session.get(fake_http + payload).json()['result']
    return info_dict

def api_get_snap_refresh():
    payload = '/v2/find?select=refresh'
    session = requests.Session()
    fake_http = "http://snapd/"
    session.mount(fake_http, wsm.snapdrequests.SnapdAdapter())
    result = session.get(fake_http + payload).json()['result']
    updatable = []
    for s in result:
        updatable.append(s['name'])
    return updatable
"""
def parse_snap_list(cmd_stdout):
    # Iterate through each line of the output.
    # TODO: Consider using PyYAML package for this (pip install PyYAML).
    snaps_list_dict = {}
    for snap_text in cmd_stdout.splitlines():
        if snap_text == cmd_stdout.splitlines()[0]:
            # Skip header line.
            continue
        # Listify the line by spaces.
        l = snap_text.decode().split()
        snap, revision = l[0], l[2]
        #notes = ''
        # TODO: Could a 'classic' snap also have other notes? Maybe needs regex.
        #if len(l) == 6 and l[5] == 'classic':
        #    notes = l[5]
        #description = api_get_snap_info(snap)['description']
        # Add snap details to dictionary.
        #snaps_list_dict[snap] = [revision, notes, description]
        snaps_list_dict[snap] = [revision]
    return snaps_list_dict

def get_snap_details(snap):
    print("Getting info for", snap, "using 'unshare' to block net access...")
    details = subprocess.run(
        ['pkexec', 'unshare', '-n', 'snap', 'info', snap, '--verbose'],
        stdout=subprocess.PIPE
    )
    info_dict = parse_snap_details(details.stdout)
    return info_dict

def parse_snap_details(output):
    lines = output.splitlines()
    info_dict = {}
    d, n = 0, 0
    for line in lines:
        line = line.decode()
        if line[0] == ' ':
            # Generally ignore indented lines...
            if d > 0:
                # ...except if part of description.
                # An earlier line, lines[d], started the description field.
                info_dict['description'] += line
            n += 1
            continue
        d = 0
        parts = line.split(':')
        key = parts[0]
        data = parts[1]
        if key == 'description':
            # Description follows on next lines.
            d = n
            data = '' # to remove initial '|'
        info_dict[key] = data
        n += 1
    return info_dict
"""
def install_snap(snap_file_path):
    base, ext = os.path.splitext(snap_file_path)
    assert_file_path = base + '.assert'

    snap_file = Path(snap_file_path)
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

def add_item_to_update_list(*args):
    # Convert list to 'set' type to eliminate duplicates.
    item_to_add = args[0]
    update_set = set(args[1])
    update_set.add(item_to_add)
    # Convert back to list before returning.
    update_list = list(update_set)
    return update_list

def snap_store_accessible():
    try:
        urllib.request.urlopen('https://api.snapcraft.io', data=None, timeout=3)
        return True
    except urllib.error.URLError:
        return False

def get_dict_from_snaps_folder(dir):
    dictionary = {}
    for assertfile in Path(dir).glob('*.assert'):
        # Each assert file is found first, then the corresponding snap file.
        snapfile = Path(dir, assertfile.stem + '.snap')
        if Path(snapfile).exists():
            # The snap file is only included if both the assert and snap exist.
            snap, rev = Path(snapfile).stem.split('_')
            dictionary[snap] = rev
    return dictionary

def list_offline_snaps(dir, init=False):
    # Called at 2 different times:
    #   1. 'wasta-offline' found automatically; i.e. init=True
    #   2. User selects an arbitrary folder; i.e. init=False

    # Get basename of given dir.
    basename = Path(dir).name
    offline_dict = {}

    # Determine if it's a wasta-offline folder.
    if init and basename != 'wasta-offline':
        # Initial folder is user's home folder.
        return offline_dict

    # Get arch in order to search correct wasta-offline folders.
    arch = platform.machine()
    if arch != 'x86_64':
        print("Arch", arch, "not supported yet for offline updates.")
        return
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
            offline_dict.update(get_dict_from_snaps_folder(folder_path))
    return offline_dict

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

def get_online_updates(snap):
    try:
        subprocess.run(['pkexec', 'snap', 'refresh', snap])
    except:
        print("Error during snap refresh.")
        return 13

def get_offline_updatable_snaps(installed_snaps_dict, offline_snaps_dict):
    updatable = []
    for snap, details in installed_snaps_dict.items():
        rev = details[0]
        if snap in offline_snaps_dict:
            if offline_snaps_dict[snap] > rev:
                updatable.append(snap)
    return updatable
"""
def get_online_updatable_snaps():
    # TODO: Get download size?
    # TODO: Use API instead?
    refresh_output = subprocess.run(
        ['snap', 'refresh', '--list'],
        stdout=subprocess.PIPE
    )
    updatable = []
    lines = refresh_output.stdout.splitlines()
    for snap_text in lines:
        if snap_text == lines[0]:
            # Skip header line.
            continue
        # Listify the line by spaces.
        l = snap_text.decode().split()
        snap, revision = l[0], l[2]
        updatable.append(snap)

    return updatable
"""
