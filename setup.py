#!/usr/bin/env python

"""
This file is part of py-sonic.

py-sonic is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

py-sonic is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with py-sonic.  If not, see <http://www.gnu.org/licenses/>
"""

from distutils.core import setup
import libsonic

setup(name='py-sonic' ,
    version=libsonic.__version__ ,
    author='Jay Deiman' ,
    author_email='admin@splitstreams.com' ,
    url='http://stuffivelearned.org' ,
    description='A python wrapper for the Subsonic REST API.  '
        'http://subsonic.org' ,
    packages=['libsonic'] ,
    package_dir={'libsonic': 'libsonic'} ,
)
