# -*- coding: utf-8 -*-

from setuptools import setup

APP = ['dockerproxy.py']
DATA_FILES = ['res']
APP_NAME = "DockerProxy"
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.icns',
    'includes': ['six', 'appdirs', 'packaging', 'packaging.version',
             'packaging.specifiers', 'packaging.requirements'],
    'plist': {
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleGetInfoString': "Containerised Web Browsing",
        'CFBundleIdentifier': "uk.co.mdsec.osx.dockerproxy",
        'CFBundleVersion': "0.1.0",
        'CFBundleShortVersionString': "0.1.0",
        'NSHumanReadableCopyright': u"Copyright © 2017, MDSec Consulting, All Rights Reserved"
    }
}
setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
