#!/app/bin/python2.7
# -*- coding: utf8 -*-
__author__ = 'gaobiling'
__verion__ = '0.5.0'
import os
import psutil
from zbxmon.monitor import Monitor

BINNAME = 'kingshard'

def discovery_kingshard(*args):
    '''
    discovery kingshard instance's host and port
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
                if opt.find('-config=') == 0:
                    config_file = opt.strip().split('=')[1]
            if os.path.exists(config_file):
                f = open(config_file, 'r')
                cfg_content = f.read()
                f.close()
            for line in cfg_content.split("\n"):
                if line.find('addr : ') == 0:
                    address = line.split(':')[1].strip()
                    port = line.split(':')[2].strip()
                    if address == '0.0.0.0':
                        address = host
                    result.append([address,port])
    return result


def get_kingshard_data(instance_name=''):
    pass

if __name__ == "__main__":
    get_kingshard_data()
