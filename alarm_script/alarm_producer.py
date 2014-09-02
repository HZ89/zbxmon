#!/usr/bin/env python2.7
# -*- coding: utf8 -*-
__author__ = 'Harrison'
import os
import sys
from time import gmtime, strftime
f = open('/tmp/zabbix-alarm-test.log', 'a+')
f.write("{}\ttype: {}\targ1: {}\targ2: {}\targ3: {}".format(strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()),
                                                            sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))