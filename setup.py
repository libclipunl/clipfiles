#!/usr/bin/env python2
from distutils.core import setup

setup(
        name='clipfiles',
        version='0.0.1',
        description='Download all your CLIP files',
        long_description="""This library allows people with credentials
to the UNL (Universidade Nova de Lisboa) CLIP system, to
download all their documents, assignments and exames, with few clicks""",
        author='David Serrano',
        author_email='david.nonamedguy@gmail.com',
        url="https://github.com/libclipunl/clipfiles",
        py_modules=['clipfiles', 'login'],
        requires=['pyclipunl'],
        license='MIT'
    )
