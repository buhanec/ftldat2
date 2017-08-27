#!/usr/bin/env python

"""Setup script."""

from setuptools import setup

from ftldat2 import __version__

setup(
    name='ftldat2',
    version=__version__,
    description='Tool for packing and unpacking FTL files.',
    author='Alen Buhanec',
    author_email='alen.buhanec@gmail.com',
    url='http://github.com/buhanec/ftldat2/',
    packages=['ftldat2'],
    package_dir={
        'ftldat2': 'ftldat2'
    },
    entry_points={
        'console_scripts': [
            'ftldat2 = ftldat2:main'
        ]
    }
)
