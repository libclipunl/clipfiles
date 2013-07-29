rmdir /s /q build
rmdir /s /q Output

setup.py build

rmdir /s /q build\exe.win32-2.7\tk\images
rmdir /s /q build\exe.win32-2.7\tk\demos
rmdir /s /q build\exe.win32-2.7\tk\msgs
rmdir /s /q build\exe.win32-2.7\tcl\tzdata
rmdir /s /q build\exe.win32-2.7\tcl\msgs


setup.iss