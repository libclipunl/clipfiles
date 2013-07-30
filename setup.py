#!/usr/bin/env python2
import sys
import os
from cx_Freeze import setup, Executable

base = None
icon = None
includes = []

if sys.platform == "win32":
    base = "Win32GUI"    # Tells the build script to hide the console.
    icon = os.path.join("img", "clip_icon.ico")
elif sys.platform == "darwin":
    icon = os.path.join("img", "clip_icon.icns")

if not icon is None:
    includes.append(icon)

build_exe_opt = {
        "optimize" : 2,
        "include_files" : includes,
        "include_msvcr" : True
}


setup(
        name='clipfiles',
        version='0.0.2',
        description='Download all your CLIP files',
        long_description="""This program allows people with credentials
to the UNL (Universidade Nova de Lisboa) CLIP system, to
download all their documents, assignments and exames, with few clicks""",
        author='David Serrano',
        author_email='david.nonamedguy@gmail.com',
        url="https://github.com/libclipunl/clipfiles",
        requires=['pyclipunl'],
        license='MIT',
        executables = [Executable("clipfiles.py", base = base, icon = icon, compress = True, shortcutName = "CLIP Files")],

        options = {
            'build_exe': build_exe_opt
        }
    )
