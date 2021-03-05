#!/usr/bin/python3
from package_dealer import package_dealer
import subprocess
import cnst

if __name__ == '__main__':
    if package_dealer():
        subprocess.call([f'./{cnst.MAIN_WINDOW_SCRIPT}'])