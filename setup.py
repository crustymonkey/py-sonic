#!/usr/bin/env python

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
