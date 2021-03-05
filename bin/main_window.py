#!/usr/bin/python3
"""
ADVC Consalting | www.advc.ru
This is the support application to help in managing input devices and charge level controlling
Application supports shortcuts to able/disable input devices ---- <Ctrl><Alt>[0-9] where [0-9] is the number of device
in the list on screen
Check README to more information
"""
import asyncio
import gi
import gbulb
import sys
import cnst
import time
import os
import yaml
import subprocess
import notify2
from device_handle import device_prop, device_map, setEnabled, Device
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
asyncio.set_event_loop_policy(gbulb.GLibEventLoopPolicy())


async def exit_check():
    while True:
        if not Gtk.main_level():
            sys.exit()
        await asyncio.sleep(0.1)


async def show_notify(msg: str):
    path2sound = f'{path}{cnst.SOUND_LOCATION}{notification_sound}'
    subprocess.call(['mpg123', path2sound], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    notifier.update(msg)
    notifier.set_urgency(notify2.URGENCY_NORMAL)
    notifier.set_timeout(10000)
    notifier.show()
    await asyncio.sleep(20)


class DeviceBox(Gtk.ListBox):
    def __init__(self):
        Gtk.ListBox.__init__(self)
        self.set_selection_mode(Gtk.SelectionMode.NONE)
        self.device_list = []

    def on_switch_activated(self, switch: Gtk.Switch, gparam=None):
        id2switch = -1
        for i in self.device_list:
            if i.switch is switch:
                id2switch = i.id
                break
        if switch.get_active():
            setEnabled(True, id2switch)
            time.sleep(0.1)
        else:
            setEnabled(False, id2switch)
            time.sleep(0.1)

    def add_device(self, input_device: Device):
        input_device.row = Gtk.ListBoxRow()
        input_device.short_cut = len(self.device_list) + 1
        hbox = BoxHelper(orientation=Gtk.Orientation.HORIZONTAL)
        input_device.row.add(hbox)
        vbox = BoxHelper(orientation=Gtk.Orientation.VERTICAL)
        hbox.pack_start(vbox, True, True, 0)
        label1 = Gtk.Label(label=input_device.name, xalign=0)
        vbox.pack_start(label1, True, True, 0)

        input_device.switch = Gtk.Switch()
        input_device.switch.props.valign = Gtk.Align.CENTER
        hbox.pack_start(input_device.switch, False, True, 0)
        if device_prop(input_device.id):
            input_device.switch.set_state(True)
        else:
            input_device.switch.set_state(False)
        input_device.switch.connect("notify::active", self.on_switch_activated)
        self.add(input_device.row)

    def clean_up(self, list_of_devices):
        for i in list_of_devices:
            self.device_list.pop(self.device_list.index(i))
        if list_of_devices:
            self.update_shortcuts()

    async def device_update(self):
        while True:
            current_devices = device_map()
            input_devices2clean = []
            current_devices_names = []
            input_devices_names = []
            for current_device in current_devices:
                current_devices_names.append(current_device.name)
            for input_device in self.device_list:
                input_devices_names.append(input_device.name)

            for input_device in self.device_list:
                if input_device.name not in current_devices_names:
                    input_devices2clean.append(input_device)
                    self.remove(input_device.row)
            self.clean_up(input_devices2clean)

            for current_device in current_devices:
                if current_device.name not in input_devices_names:
                    self.add_device(current_device)
                    self.device_list.append(current_device)
            self.show_all()
            await asyncio.sleep(1)

    def update_shortcuts(self):
        for i, dvc in enumerate(self.device_list):
            dvc.short_cut = i + 1

    def key_press_event(self, widget, event):
        keyval = event.keyval
        keyval_name = Gdk.keyval_name(keyval)
        state = event.state
        ctrl = (state & (Gdk.ModifierType.MOD1_MASK | Gdk.ModifierType.CONTROL_MASK))
        try:
            for input_device in self.device_list:
                if ctrl and input_device.short_cut == int(keyval_name):
                    switch_state = not input_device.switch.get_active()
                    input_device.switch.set_active(switch_state)
                    setEnabled(switch_state, input_device.id)
                    return True
        except ValueError:
            return False


class BatteryBox(Gtk.ListBox):
    def __init__(self):
        Gtk.ListBox.__init__(self)
        self.power_value = float()
        self.close_window_flag = False
        self.power_val_label = Gtk.Label(label='power_rate', xalign=0)
        self.AC_val_label = Gtk.Label(label='AC', xalign=0)
        self.battery_list_box = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        self.battery_list_box.add(hbox)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox.pack_start(vbox, True, True, 0)
        power_label = Gtk.Label(label='Charge level /', xalign=0)
        AC_label = Gtk.Label(label="On charge", xalign=0)
        hbox.pack_start(self.power_val_label, True, True, 0)
        vbox.pack_start(power_label, True, True, 0)
        vbox.pack_start(AC_label, True, True, 0)
        hbox.pack_start(self.AC_val_label, True, True, 0)
        self.add(self.battery_list_box)

    async def charge_update(self):
        while True:
            with open(f'{cnst.BAT_LOCATION}{cnst.CHARGE_PERCENT}', 'r') as charge:
                self.power_value = int(charge.read()[:-1])
            self.power_val_label.set_label(f'{self.power_value}%')
            await asyncio.sleep(5)

    async def ac_check(self):
        global AC_flag
        while True:
            with open(f'{cnst.AC_LOCATION}{cnst.ONLINE}', 'r') as online:
                online_value = int(online.read()[0])
            if online_value:
                AC_flag = True
                self.AC_val_label.set_markup("<span font_desc='Tahoma 15'>✔</span>")
            else:
                AC_flag = False
                self.AC_val_label.set_markup("<span font_desc='Tahoma 15'>✘</span>")
            warn_entry.set_editable(not AC_flag)
            critical_entry.set_editable(not AC_flag)
            await asyncio.sleep(2)

    async def warning_check(self):
        while True:
            if self.power_value <= warning_charge_value and not AC_flag:
                await show_notify(
                    f'Low battery. {self.power_value - critical_charge_value if self.power_value > critical_charge_value else 0}'
                    f' percent of charge left before switching to suspend')
            await asyncio.sleep(3)

    async def critical_check(self):
        while True:
            if self.power_value <= critical_charge_value and not AC_flag:
                critical_window = Gtk.Window(title='Attention!')
                critical_window.set_border_width(10)
                critical_window.set_size_request(100, 50)
                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
                label = Gtk.Label()
                box.pack_start(label, True, True, 0)
                ok_button = Gtk.Button.new_with_mnemonic("No!")
                ok_button.connect("clicked", self.suspend_deny_on_click)
                box.pack_start(ok_button, True, True, 0)
                critical_window.add(box)
                critical_window.show_all()
                for i in range(11):
                    label.set_label(f'Charge level is lower than critical. Laptop is going to suspend in {10 - i} sec')
                    if self.close_window_flag:
                        critical_window.destroy()
                        self.close_window_flag = False
                        await asyncio.sleep(20)
                        return loop.create_task(self.critical_check())
                    await asyncio.sleep(1)
                subprocess.call(['systemctl', 'suspend'])
            await asyncio.sleep(1)

    def suspend_deny_on_click(self, button: Gtk.Button):
        self.close_window_flag = True


def settings_box_init():
    box = BoxHelper()
    box.set_border_width(10)
    box.add(entries_init
                    ('warning charge level', warn_entry, warning_charge_value, warning_ok_click, warning_delete_click, max_length=2))
    box.add(entries_init
                    ('critical charge level   ', critical_entry, critical_charge_value, critical_ok_click, critical_delete_click, max_length=2))
    box.add(entries_init(f'icon{33*" "}', icon_entry, icon, icon_on_click, icon_delete_click))
    box.add(entries_init(f'sound{29*" "}', sound_entry, notification_sound, sound_ok_click, sound_delete_click))
    return box


def entries_init(label, entry, init_value, callback_ok, callback_delete, max_length=100):
    entry_box = Gtk.ListBoxRow()
    hbox = BoxHelper(orientation=Gtk.Orientation.HORIZONTAL)
    entry_box.add(hbox)
    vbox = BoxHelper()
    hbox.pack_start(vbox, True, True, 0)
    warn_label = Gtk.Label(label=label, xalign=0)
    vbox.pack_start(warn_label, True, True, 0)

    entry.set_max_length(max_length)
    entry.set_text(str(init_value))
    hbox.pack_start(entry, False, True, 0)

    image = Gtk.Image(stock=Gtk.STOCK_OK)
    ok_button = Gtk.Button(image=image)
    ok_button.connect("clicked", callback_ok)
    hbox.pack_start(ok_button, True, True, 0)

    image = Gtk.Image(stock=Gtk.STOCK_DELETE)
    ok_button = Gtk.Button(image=image)
    ok_button.connect("clicked", callback_delete)
    hbox.pack_start(ok_button, True, True, 0)
    return entry_box


def icon_on_click(button: Gtk.Button):
    global icon
    text = icon_entry.get_text()
    if not os.path.isfile(f'{path}{cnst.ICON_LOCATION}{text}'):
        message_window('No such file in ~/resources/image/', 'Error')
        return
    icon = text
    update_cache(cnst.ICON, icon)


def icon_delete_click(button: Gtk.Button):
    icon_entry.set_text('')


def sound_ok_click(button: Gtk.Button):
    global notification_sound
    text = sound_entry.get_text()
    if not os.path.isfile(f'{path}{cnst.SOUND_LOCATION}{text}'):
        message_window('No such file in ~/resources/sound/', 'Error')
        return
    notification_sound = text
    update_cache(cnst.NOTIFICATION_SOUND, notification_sound)


def sound_delete_click(button: Gtk.Button):
    sound_entry.set_text('')


def warning_ok_click(button: Gtk.Button):
    global warning_charge_value
    global critical_charge_value
    text = warn_entry.get_text()
    if AC_flag:
        message_window('Laptop is on charge', 'Notification')
        return
    if text.isdigit() and int(text) > 0:
        warning_charge_value = int(text)
        update_cache(cnst.WARN, warning_charge_value)
        if warning_charge_value < critical_charge_value:
            warning_charge_value = critical_charge_value
            warn_entry.set_text(str(warning_charge_value))
            message_window('Warning charge level is lower then critical', 'Warning')
    else:
        warning_delete_click(button)
        message_window('Invalid data. Input must be a positive number', 'Error')


def warning_delete_click(button: Gtk.Button):
    warn_entry.set_text('')


def critical_ok_click(button: Gtk.Button):
    global critical_charge_value
    global warning_charge_value
    text = critical_entry.get_text()
    if AC_flag:
        message_window('Laptop is on charge', 'Notification')
        return
    if text.isdigit() and int(text) > 0:
        critical_charge_value = int(text)
        update_cache(cnst.CRIT, critical_charge_value)
        if critical_charge_value > warning_charge_value:
            warning_charge_value = critical_charge_value
            warn_entry.set_text(str(critical_charge_value))
            message_window('Critical charge level is bigger the warning charge level', 'Warning')
    else:
        critical_delete_click(button)
        message_window('Invalid data. Input must be a positive number', 'Error')


def critical_delete_click(button: Gtk.Button):
    critical_entry.set_text('')


def message_window(text: str, title: str):
    WindowHelper([Gtk.Label(label=text)], title, 200, 100)


def update_cache(parameter: str, val):
    with open(f'{path}{cnst.CACHE}/{parameter}', 'w') as wrn:
        wrn.write(str(val))


class WindowHelper(Gtk.Window):
    def __init__(self, items=[], title='', high=None, width=None):
        Gtk.Window.__init__(self, title=title)
        self.set_border_width(3)
        if high and width: self.set_size_request(high, width)
        for item in items:
            self.add(item)
        self.show_all()


class NotebookHelper(Gtk.Notebook):
    def __init__(self, pages=[]):
        Gtk.Notebook.__init__(self)
        for page, label in pages:
            self.append_page(page, label)
        self.show_all()


class BoxHelper(Gtk.Box):
    def __init__(self, list_box=[], orientation=Gtk.Orientation.VERTICAL):
        Gtk.Box.__init__(self, orientation=orientation, spacing=10)
        for element in list_box:
            self.pack_start(element, True, True, 0)


def init():
    global warning_charge_value
    global critical_charge_value
    global icon
    global notification_sound
    if not os.path.isdir(f'{path}{cnst.CACHE}'):
        os.mkdir(f'{path}{cnst.CACHE}')
        with open(f'{path}{cnst.CONFIG_LOCATION}', 'r') as f:
            config_data = yaml.load(f, Loader=yaml.FullLoader)
        for var in config_data.items():
            name, value = var
            if type(value) is int: exec("%s = %d" % (name, value), globals())
            else:
                exec("%s = \"%s\"" % (name, value), globals())
            update_cache(name, value)
    else:
        for i in os.listdir(f'{path}{cnst.CACHE}'):
            with open(f'{path}{cnst.CACHE}/{i}', 'r') as ch:
                var = ch.read().strip()
                if var.isdigit(): exec("%s = %d" % (i, int(var)), globals())
                else: exec("%s = \"%s\"" % (i, var), globals())


def builder():
    device = DeviceBox()
    input_device_label = Gtk.Label()
    input_device_label.set_markup("<span font_desc='Tahoma 12'>\n Input devices</span>")
    device_box = BoxHelper([input_device_label, device])

    battery = BatteryBox()
    battery_label = Gtk.Label()
    battery_label.set_markup("<span font_desc='Tahoma 12'>Battery</span>")
    battery_box = BoxHelper([battery_label, battery])

    main_page = BoxHelper([device_box, battery_box])

    # 2 tab
    setting_box = settings_box_init()

    # Push tabs into notebook
    notebook = NotebookHelper([(main_page, Gtk.Label(label="Main")), (setting_box, Gtk.Label(label="Settings"))])

    # Fill event loop
    for func in [device.device_update(), exit_check(), battery.charge_update(), battery.ac_check(),
                 battery.warning_check(), battery.critical_check()]:
        loop.create_task(func)

    win = WindowHelper([notebook], 'ADVC_helper')
    win.connect("destroy", Gtk.main_quit)
    win.connect("key-press-event", device.key_press_event)

    # Run GUI
    Gtk.main()


if __name__ == '__main__':

    # Initial values
    AC_flag = False
    path = os.getcwd()[:-3]
    warning_charge_value = float()
    critical_charge_value = float()
    icon = ''
    notification_sound = ''
    warn_entry = Gtk.Entry()
    critical_entry = Gtk.Entry()
    icon_entry = Gtk.Entry()
    sound_entry = Gtk.Entry()

    # Notifier init
    notify2.init('ADVC')
    notifier = notify2.Notification("Battery Notifier")

    # Initialize event loop
    loop = asyncio.get_event_loop()

    # Initialize values from config
    init()

    # Build GUI
    builder()

    # Run event loop
    loop.run_forever()

