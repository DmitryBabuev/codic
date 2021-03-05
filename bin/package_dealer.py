import cnst
import os
import re
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def os_detection():
    package_manager = None
    if os.path.isfile(cnst.OS_INFO):
        with open(cnst.OS_INFO, 'r') as os_info_pointer:
            os_info = os_info_pointer.read()
        os_type = re.search(r'ID=\S*', os_info)[0][3:].replace('\"', '').lower()
        if cnst.CENTOS in os_type:
            package_manager = cnst.CENTOS_PACKAGE_MANAGER
        elif cnst.UBUNTU or cnst.MINT in os_type:
            package_manager = cnst.UBUNTU_PACKAGE_MANAGER
    return package_manager


def package_detector():
    packages2install = ''
    notify2_pack = os.path.isfile(cnst.PACKAGE_LOCATION_NOTIFY2)
    gbulb_pack = os.path.isdir(cnst.PACKAGE_LOCATION_GBULB)
    mpg123_pack = os.path.isfile(cnst.PACKAGE_LOCATION_MPG123)
    if not notify2_pack:
        packages2install += f'{cnst.PACKAGE_NAME_NOTIFY2} '
    if not gbulb_pack:
        packages2install += f'{cnst.PACKAGE_NAME_GBULB} '
    if not mpg123_pack:
        packages2install += f'{cnst.PACKAGE_NAME_MPG123} '
    return packages2install


def install_package_display(command: str):
    notify_window = Gtk.Window(title=f'WHAT\'s GOOOD DUDE')
    notify_window.set_border_width(10)
    notify_window.set_size_request(100, 50)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    label_comment = Gtk.Label()
    label_comment.set_label('You need to run the following command in your terminal and rerun the application')
    label = Gtk.Label()
    label.set_selectable(True)
    command = "<span font_desc='Tahoma 14'>{command}</span>".format(command=command)
    label.set_markup(command)
    for i in [label_comment, label]: box.pack_start(i, True, True, 0)
    notify_window.connect("destroy", Gtk.main_quit)
    notify_window.add(box)
    notify_window.show_all()
    Gtk.main()


def package_dealer():
    needed_packages = package_detector()[:-1]
    if needed_packages:
        package_manager = os_detection()
        if not package_manager: pass
        install_package_display(f'sudo {package_manager} install -y {needed_packages}')
        return
    return True

