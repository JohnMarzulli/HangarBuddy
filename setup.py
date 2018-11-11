import lib.local_debug as local_debug
import configuration
from setuptools import setup

installs = ['pytest',
            'pyserial']


setup(name='HangarBuddy',
      version='1.2',
      python_requires='>=2.7',
      description='Raspberry Pi based tool to remotely monitor and control an engine pre-heater.',
      url='https://github.com/JohnMarzulli/HangarBuddy',
      author='John Marzulli',
      author_email='john.marzulli@hotmail.com',
      license='GPL V3',
      install_requires=installs
      )
