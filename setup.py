#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
from io import open
from os.path import dirname, join

import distutils
from setuptools import setup, find_packages


def read(*args):
    return open(join(dirname(__file__), *args), encoding='utf-8').read()


class ToxTestCommand(distutils.cmd.Command):
    """Distutils command to run tests via tox with 'python setup.py test'.

    Please note that in our standard configuration tox uses the dependencies in
    `requirements/dev.txt`, the list of dependencies in `tests_require` in
    `setup.py` (if present) is ignored!

    See https://docs.python.org/3/distutils/apiref.html#creating-a-new-distutils-command
    for more documentation on custom distutils commands.

    """
    description = "Run tests via 'tox'."
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.announce("Running tests with 'tox'...", level=distutils.log.INFO)
        return subprocess.call(['tox'])


exec(read('src', 'xair', 'version.py'))

classifiers = """\
Development Status :: 3 - Alpha
#Environment :: MacOS X
#Environment :: Win32 (MS Windows)
Intended Audience :: Developers
Intended Audience :: Other Audience
Intended Audience :: Telecommunications Industry
License :: OSI Approved :: MIT License
Natural Language :: English
#Natural Language :: German
Operating System :: MacOS :: MacOS X
#Operating System :: Microsoft :: Windows
Operating System :: POSIX :: Linux
Programming Language :: Python :: 3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Topic :: Home Automation
Topic :: Multimedia :: Sound/Audio
Topic :: Multimedia :: Sound/Audio :: Mixers
Topic :: Multimedia :: Sound/Audio :: MIDI
Topic :: Software Development :: Testing
Topic :: System :: Networking
"""

install_requires = [
    'cmd2',
    'pyliblo',
    'python-rtmidi',
]


setup(
    name='xair-remote',
    version=__version__,  # noqa:F821
    author='Christopher Arndt',
    author_email='info@chrisarndt.de',
    description='Tools for querying and controlling Behringer X-AIR and MIDAS M-AIR audio mixers',
    long_description=read('README.rst'),
    url='https://github.com/SpotlightKid/xair-remote',
    license='MIT',
    keywords=("music, MIDI, OSC, automation, Python, Behringer, MIDAS"),
    classifiers=[c for c in (c.strip() for c in classifiers.splitlines())
                 if c and not c.startswith('#')],
    package_dir={'':'src'},
    packages=find_packages('src'),
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'xaircmd=xair.xaircmd:main'
        ]
    },
    cmdclass={'test': ToxTestCommand},
    zip_safe=False
)
