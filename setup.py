#!/usr/bin/env python
import os
from setuptools import setup, find_packages


setup(name='tim',
        version = '0.2',
        install_requires=[
            'argparse>=1.1'
            ],
        #  packages = ['cronwrap/cw', 'cronwrap/scripts'],
        packages = find_packages(),
        entry_points={'console_scripts': ['tim=tim.timscript:main']}
        )

