#!/usr/bin/env python
# -*- coding: utf8 -*-

import os
from distutils.core import setup


setup(
    name='zbxmon',
    version='0.1.2',
    packages=['zbxmon', 'zbxmon/lib'],
    provides=['zbxmon'],
    url='https://github.com/damagedcode/zbxmon',
    license='MIT',
    author='Harrison Zhu && Justin Ma',
    author_email='wcg6121@gmail.com',
    description='A script for zabbix agent monitor service, etc. mysql, mongodb, memcache..',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r').read(),
    scripts=[
        'scripts/zbxmon',
    ],
    requires=['psutil', 'netifaces', 'pymongo', 'python-memcached']
)

