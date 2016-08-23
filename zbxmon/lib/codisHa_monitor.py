#!/app/bin/python2.7
# -*- coding: utf8 -*-
__author__ = 'gaobiling'
__verion__ = '0.5.0'
import os
import psutil
from zbxmon.monitor import Monitor

BINNAME = 'codis-ha'


def discovery_codisHa(*args):
    '''
    discovery codis-ha instance's host and port
    '''
    result = []
    port = ''
    address = ''
    cmdline = []
    host = Monitor.get_local_ip()
    for i in psutil.process_iter():
        if i.name() == BINNAME:
            pid = int(i.pid)
            cmdline = i.cmdline()

            for opt in cmdline:
                if opt.find('--dashboard=') == 0:
                    address = opt.strip().split('=')[1].split(':')[0].strip()
                    port = opt.strip().split('=')[1].split(':')[1].strip()
                    result.append([address, port])
    return result


def get_codisHa_data(instance_name=''):
    pass


if __name__ == "__main__":
    get_codisHa_data()
