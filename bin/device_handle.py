import subprocess
import sys
import re


class Device:
    def __init__(self, device_name, device_id, switch=None, short_cut=None, row=None):
        self.name = device_name
        self.id = device_id
        self.switch = switch
        self.short_cut = short_cut
        self.row = row


def device_map():
    try:
        data = subprocess.check_output(['xinput', '--list'])
    except Exception:
        print("xinput not found!")
        sys.exit()
    devices = []
    data = data.decode("utf-8")
    for line in data.splitlines():
        line = line.lower().strip()
        if 'pointer' in line and 'slave' in line and 'virtual core' not in line:
            match = re.search(r'id=([0-9]+)', line)
            device_id = str(match.group(1))
            devices.append(Device(device_name=line.split('\t')[0].strip()[6:], device_id=device_id))
    return devices


def device_prop(device_id: str):
    prop_data = subprocess.check_output(['xinput', '--list-props', device_id])
    prop_data = prop_data.decode()
    for line in prop_data.splitlines():
        if 'Device Enabled' in line and line.strip()[-1] == '1':
            return True
        elif 'Device Enabled' in line and line.strip()[-1] == '0':
            return False


def setEnabled(state: bool, device_id: str):
    if state:
        flag = '--enable'
    else:
        flag = '--disable'
    try:
        subprocess.check_call(['xinput', flag, device_id])
    except Exception:
        pass