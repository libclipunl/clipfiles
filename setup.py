#!/usr/bin/env python2
import sys
import os
import subprocess
import traceback

from cx_Freeze import setup, Executable
from clipfiles import VERSION

ISS_FILE="setup.iss"

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
        version=VERSION,
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

if sys.platform == "win32":
    try:
        if len(sys.argv) > 1:
            if sys.argv[1] == "build":
                # Run Inno Setup compiler
                call = [
                    "ISCC.EXE",
                    "/dMyAppVersion=%s" % (VERSION,),
                    ISS_FILE
                ]
                print call
                subprocess.call(call)

                print "Inno Setup package build successfully"
    except:
        traceback.print_exc(sys.stdout)
        print "Unable to build Inno setup package"

