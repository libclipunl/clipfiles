#!/usr/bin/env python2
import sys
import os
import subprocess
import traceback

from cx_Freeze import setup, Executable
from clipfiles import VERSION, IMAGES, ICON_FILE

ISS_FILE="setup.iss"

base = None
icon = ICON_FILE
includes = []

if sys.platform == "win32":
    base = "Win32GUI"    # Tells the build script to hide the console.

if not icon is None:
    includes.append(icon)

includes = includes + IMAGES.values()

build_exe_opt = {
        "optimize" : 2,
        "include_files" : includes,
        "include_msvcr" : True
}

to_delete = [
        os.path.join("tcl", "encoding"),
        os.path.join("tcl", "http1.0"),
        os.path.join("tcl", "msgs"),
        os.path.join("tcl", "tzdata"),
        os.path.join("tcl", "opt0.4"),
        
        os.path.join("tk", "demos"),
        os.path.join("tk", "images"),
        os.path.join("tk", "msgs")
    ]


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

if len(sys.argv) > 0 and sys.argv[1] == "build":
    print "Deleting Fat"
    import shutil
    for f in to_delete:
        to_del = os.path.join("build", "exe.%s-2.7" % (sys.platform,),f)
        print "Removing: %s" % (to_del,)
        shutil.rmtree(to_del)

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

