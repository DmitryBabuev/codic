#!/usr/bin/python3
import gi
import sys
import os
import subprocess
import notify2
import asyncio
import gbulb
import cnst
import time
from device_handle import device_prop, device_map, setEnabled
gi.require_version("Gtk", "3.0")
gi.require_version('Keybinder', '3.0')
from gi.repository import Gtk, Gdk
asyncio.set_event_loop_policy(gbulb.GLibEventLoopPolicy())


def on_switch_activated(switch: Gtk.Switch, gparam=None):
    if switch.get_active():
        setEnabled(True, switch_map.get(switch))
        time.sleep(0.1)
    else:
        setEnabled(False, switch_map.get(switch))
        time.sleep(0.1)


async def show_notify(msg: str):
    subprocess.call(['mpg123', 'sound.mp3'], stdout=devnull, stderr=devnull)
    notifier.update(msg)
    notifier.set_urgency(notify2.URGENCY_NORMAL)
    notifier.set_timeout(10000)
    notifier.show()
    await asyncio.sleep(20)


async def exit_check():
    while True:
        if not Gtk.main_level():
            sys.exit()
        await asyncio.sleep(1)


async def charge_update():
    global power_value
    while True:
        with open(f'{cnst.BAT_DIR}{cnst.CHARGE_PERCENT}', 'r') as charge:
            power_value = int(charge.read()[:-1])
        power_val_label.set_label(f'{power_value}%')
        await asyncio.sleep(5)


async def ac_check():
    global AC_flag
    while True:
        with open(f'{cnst.AC_DIR}{cnst.ONLINE}', 'r') as online:
            online_value = int(online.read()[0])
        if online_value:
            AC_flag = True
            AC_val_label.set_markup("<span font_desc='Tahoma 15'>✔</span>")
        else:
            AC_flag = False
            AC_val_label.set_markup("<span font_desc='Tahoma 15'>✘</span>")
        warn_entry.set_editable(not AC_flag)
        critical_entry.set_editable(not AC_flag)
        await asyncio.sleep(2)


async def warning_check():
    while True:
        if power_value <= warning_value and not AC_flag:
            await show_notify(f'Low battery. {power_value-critical_value if power_value > critical_value else 0}'
                              f' percent of charge left before switching to suspend')
        await asyncio.sleep(3)


async def critical_check():
    global go2suspend_flag
    while True:
        if power_value <= critical_value and not AC_flag:
            critical_window = Gtk.Window(title='Attention!')
            critical_window.set_border_width(10)
            critical_window.set_size_request(100, 50)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            label = Gtk.Label()
            box.pack_start(label, True, True, 0)
            ok_button = Gtk.Button.new_with_mnemonic("No!")
            ok_button.connect("clicked", suspend_deny_on_click)
            box.pack_start(ok_button, True, True, 0)
            critical_window.add(box)
            critical_window.show_all()
            for i in range(11):
                label.set_label(f'Charge level is lower than critical. Laptop is going to suspend in {10-i} sec')
                if not go2suspend_flag:
                    critical_window.destroy()
                    go2suspend_flag = True
                    await asyncio.sleep(20)
                    break
                elif go2suspend_flag and i == 10:
                    sys.exit()
                await asyncio.sleep(1)
        await asyncio.sleep(1)


def suspend_deny_on_click(button: Gtk.Button):
    global go2suspend_flag
    go2suspend_flag = False


def warning_ok_click(button: Gtk.Button):
    global warning_value
    global critical_value
    text = warn_entry.get_text()
    if AC_flag:
        error_message('Laptop is on charge', 'Notification')
        return
    if text.isdigit():
        warning_value = int(text)
        update_cache(warning_value, 'warn')
        if warning_value < critical_value:
            warning_value = critical_value
            warn_entry.set_text(str(warning_value))
            error_message('Warning charge level is lower then critical', 'Warning')
    else:
        warning_delete_click(button)
        error_message('Invalid data. Input must be a positive number', 'Error')


def warning_delete_click(button: Gtk.Button):
    warn_entry.set_text('')


def critical_ok_click(button: Gtk.Button):
    global critical_value
    global warning_value
    text = critical_entry.get_text()
    if AC_flag:
        error_message('Laptop is on charge', 'Notification')
        return
    if text.isdigit():
        critical_value = int(text)
        update_cache(critical_value, 'crit')
        if critical_value > warning_value:
            warning_value = critical_value
            warn_entry.set_text(str(critical_value))
            error_message('Critical charge level is bigger the warning charge level', 'Warning')
    else:
        critical_delete_click(button)
        error_message('Invalid data. Input must be a positive number', 'Error')


def critical_delete_click(button: Gtk.Button):
    critical_entry.set_text('')


def error_message(error_text: str, error_title: str):
    error_window = Gtk.Window(title=error_title)
    error_window.set_border_width(10)
    error_window.set_size_request(200, 100)
    error_label = Gtk.Label()
    error_label.set_label(error_text)
    error_window.add(error_label)
    error_window.show_all()


def first_init():
    if not os.path.isdir(f'{cnst.CACHE}'):
        os.mkdir(f'{cnst.CACHE}')
        with open(f'{cnst.CACHE}/{cnst.WARN}', 'w') as wrn:
            wrn.write(str(warning_value))
        with open(f'{cnst.CACHE}/{cnst.CRIT}', 'w') as crt:
            crt.write(str(critical_value))


def read_cache():
    global warning_value
    global critical_value
    if os.path.isfile(f'{cnst.CACHE}/{cnst.WARN}'):
        with open(f'{cnst.CACHE}/{cnst.WARN}', 'r') as wrn:
            warning_value = int(wrn.read())
    if os.path.isfile(f'{cnst.CACHE}/{cnst.CRIT}'):
        with open(f'{cnst.CACHE}/{cnst.CRIT}', 'r') as crt:
            critical_value = int(crt.read())


def update_cache(val: int, flag: str):
    if flag == 'warn':
        with open(f'{cnst.CACHE}/{cnst.WARN}', 'w') as wrn:
            wrn.write(str(val))
    elif flag == 'crit':
        with open(f'{cnst.CACHE}/{cnst.CRIT}', 'w') as crt:
            crt.write(str(val))


def key_press_event(widget, event):
    keyval = event.keyval
    keyval_name = Gdk.keyval_name(keyval)
    state = event.state
    ctrl = (state & (Gdk.ModifierType.MOD1_MASK | Gdk.ModifierType.CONTROL_MASK))
    if ctrl and shortcut_map.get(int(keyval_name)):
        switch = shortcut_map.get(int(keyval_name))
        switch_state = not switch.get_active()
        switch.set_active(switch_state)
        setEnabled(switch_state, switch_map.get(switch))
    else:
        return False
    return True



def main():
    # First run
    first_init()

    # Check cache
    read_cache()

    # Main window init
    window = Gtk.Window(title='ADVC helper :)')
    window.set_border_width(10)

    # Tabs init
    notebook = Gtk.Notebook()

    # Main tab
    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

    input_label = Gtk.Label()
    input_label.set_markup("<span font_desc='Tahoma 12'>\n Input devices</span>")

    main_box.pack_start(input_label, True, True, 0)

    notebook.append_page(main_box, Gtk.Label(label="Main"))

    setting_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    setting_box.set_border_width(10)

    notebook.append_page(setting_box, Gtk.Label(label="Settings"))
    window.add(notebook)

    # Get info about input devices
    devices = device_map()

    # Input devices switch bar
    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.NONE)
    main_box.pack_start(listbox, True, True, 0)

    i = 1
    for item in devices.items():
        device_name, device_id = item
        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        row.add(hbox)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox.pack_start(vbox, True, True, 0)

        label1 = Gtk.Label(label=device_name, xalign=0)
        vbox.pack_start(label1, True, True, 0)

        switch = Gtk.Switch()
        switch_map.setdefault(switch, device_id)
        shortcut_map.setdefault(i, switch)

        switch.props.valign = Gtk.Align.CENTER
        hbox.pack_start(switch, False, True, 0)
        if device_prop(device_id):
            switch.set_state(True)
        else:
            switch.set_state(False)
        switch.connect("notify::active", on_switch_activated)
        listbox.add(row)
        i += 1

    # Battery bar
    battery_label = Gtk.Label()
    battery_label.set_markup("<span font_desc='Tahoma 12'>Battery</span>")
    main_box.pack_start(battery_label, True, True, 0)
    listbox = Gtk.ListBox()
    listbox.set_selection_mode(Gtk.SelectionMode.NONE)
    main_box.pack_start(listbox, True, True, 0)

    row = Gtk.ListBoxRow()
    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
    row.add(hbox)
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    hbox.pack_start(vbox, True, True, 0)

    power_label = Gtk.Label(label='Charge level /', xalign=0)
    AC_label = Gtk.Label(label="On charge", xalign=0)
    hbox.pack_start(power_val_label, True, True, 0)
    vbox.pack_start(power_label, True, True, 0)
    vbox.pack_start(AC_label, True, True, 0)
    hbox.pack_start(AC_val_label, True, True, 0)
    listbox.add(row)

    # Settings tab
    row = Gtk.ListBoxRow()
    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    row.add(hbox)
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    hbox.pack_start(vbox, True, True, 0)
    warn_label = Gtk.Label(label='warning charge level', xalign=0)
    vbox.pack_start(warn_label, True, True, 0)

    warn_entry.set_max_length(2)
    warn_entry.set_text(str(warning_value))
    hbox.pack_start(warn_entry, False, True, 0)

    image = Gtk.Image(stock=Gtk.STOCK_OK)
    ok_button = Gtk.Button(image=image)
    ok_button.connect("clicked", warning_ok_click)
    hbox.pack_start(ok_button, True, True, 0)

    image = Gtk.Image(stock=Gtk.STOCK_DELETE)
    ok_button = Gtk.Button(image=image)
    ok_button.connect("clicked", warning_delete_click)
    hbox.pack_start(ok_button, True, True, 0)

    setting_box.add(row)

    # Critical charge level
    row = Gtk.ListBoxRow()
    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    row.add(hbox)
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    hbox.pack_start(vbox, True, True, 0)
    warn_label = Gtk.Label(label='critical charge level   ', xalign=0)
    vbox.pack_start(warn_label, True, True, 0)

    critical_entry.set_max_length(2)
    critical_entry.set_text(str(critical_value))
    hbox.pack_start(critical_entry, False, True, 0)

    image = Gtk.Image(stock=Gtk.STOCK_OK)
    ok_button = Gtk.Button(image=image)
    ok_button.connect("clicked", critical_ok_click)
    hbox.pack_start(ok_button, True, True, 0)

    image = Gtk.Image(stock=Gtk.STOCK_DELETE)
    ok_button = Gtk.Button(image=image)
    ok_button.connect("clicked", critical_delete_click)
    hbox.pack_start(ok_button, True, True, 0)

    setting_box.add(row)

    # Async loop
    for funcs in [charge_update(), warning_check(), exit_check(), critical_check(), ac_check()]:
        loop.create_task(funcs)

    # GTK main
    window.connect("destroy", Gtk.main_quit)
    window.connect("key-press-event", key_press_event)
    window.show_all()
    Gtk.main()

    loop.run_forever()


if __name__ == '__main__':
    # /dev/null
    devnull = os.open(os.devnull, os.O_WRONLY)

    # Notifier
    notify2.init('ipamd')
    notifier = notify2.Notification("Battery Notifier")

    # Loop launch
    loop = asyncio.get_event_loop()

    # Gtk labels for charge % and power on\off
    power_val_label = Gtk.Label(label='power_rate', xalign=0)
    AC_val_label = Gtk.Label(label='AC', xalign=0)

    # Gtk entries
    warn_entry = Gtk.Entry()
    critical_entry = Gtk.Entry()

    # Default values
    warning_value = 20
    critical_value = 5
    power_value = 100

    # Hash map for switches
    switch_map = {}
    shortcut_map = {}

    # Flags
    go2suspend_flag = True
    AC_flag = True

    main()
