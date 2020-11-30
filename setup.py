#!/usr/bin/env python

from setuptools import setup

from lib.local_debug import IS_PI

installs = ['pyserial']

if IS_PI:
    installs += 'RPi.GPIO'
    installs += 'smbus2'

setup(
    name='HangarBuddy',
    version='1.5',
    python_requires='>=3.5',
    description='Service to run hangar automation tools and monitoring.',
    author='John Marzulli',
    author_email='john.marzulli@outlook.com',
    url='https://github.com/JohnMarzulli/HangarBuddy',
    license='GPL V3',
    install_requires=installs)
