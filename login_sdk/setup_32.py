# -*- coding: utf-8 -*-

import os
import shutil
import sys
from cx_Freeze import setup, Executable


include_res = os.path.join(os.getcwd(), 'res')
platform_dir = os.path.join(os.getcwd(), 'x32')
include_platforms = os.path.join(platform_dir, 'platforms')
icon = os.path.join(include_res, 'favicon.ico')

base = None
if sys.platform == "win32":
    base = "Win32GUI"

build_exe_optoins = {
    'includes': ['win32timezone'],
    'excludes': ['tkinter'],
    'include_files': [include_res],
}

options = {
    'build_exe': build_exe_optoins,
}

executables = [
    Executable('rdp_login.py', base=base, icon=icon)
]

setup(
    name = 'pandora',
    version = '1.0',
    description = 'pandora',
    options = options,
    executables = executables,
)

# copy platforms to build
build_folder = os.path.join(os.getcwd(), 'build')
program_folder = os.path.join(build_folder, os.listdir(build_folder)[0])
shutil.copytree(include_platforms, os.path.join(program_folder, 'platforms'))
