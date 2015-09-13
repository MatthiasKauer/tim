#!/usr/bin/env python
import os
from setuptools import setup, find_packages
from tim import __version__

#PyPI guide: https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/
def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

setup(
    name='tim-timetracker',
    version = __version__,
    install_requires=[
        'argparse>=1.1',
        'parsedatetime>=1.2',
        'colorama>=0.3.0',
        'pyyaml>=3.0',
        'tzlocal>=1.2',
        'pytz>=2015.2',
        ],
    packages = find_packages(),
    entry_points={'console_scripts': ['tim=tim.timscript:main']},
    description="command line time logger with hledger backend for number crunching",
    long_description=(read('README.md') + "\n\n" + 
                    read("AUTHORS.md")),
    license="MIT",
    author="Matthias Kauer",
    author_email="mk.software@zuez.org",
    url="https://github.com/MatthiasKauer/tim",
    platforms=["Any"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        ],
)

