#!/usr/bin/env python3

"""
This file is part of py-opensonic.

py-sonic is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

py-opensonic is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with py-opensonic.  If not, see <http://www.gnu.org/licenses/>
"""

import re
from pathlib import Path
from setuptools import setup,find_packages



# read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
requirements = (this_directory / 'requirements.txt').read_text()

# Get package __version__ in our namespace
ver_path = this_directory / 'src' / 'libopensonic' / '_version.py'
verstr = 'unknown'
try:
    verstrline = open(ver_path, "rt", encoding='utf-8').read()
except EnvironmentError:
    pass # Okay, there is no version file.
else:
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        verstr = mo.group(1)
    else:
        raise RuntimeError("unable to find version in yourpackage/_version.py")

setup(name='py-opensonic',
    version=verstr,
    author='Eric B. Munson',
    author_email='eric@munsonfam.org',
    url='https://github.com/khers/py-opensonic',
    description='A python wrapper library for the Open Subsonic REST API.  '
        'https://opensubsonic.netlify.app/',
    long_description=long_description,
    long_description_content_type='text/markdown',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    py_modules=['libopensonic'],
    install_requires=requirements,
    python_requires='>=3',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: System :: Systems Administration',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries',
        'Topic :: System',
    ]
)
