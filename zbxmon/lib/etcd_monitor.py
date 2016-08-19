#!/app/bin/python2.7
# -*- coding: utf8 -*-
__author__ = 'gaobiling'
__verion__ = '0.5.0'
import os
import re
import psutil
import commands
from zbxmon.monitor import Monitor

BINNAME = 'etcd'
CFG_DIR = '/etc/etcd/'

def discovery_etcd():
    '''
    discovery etcd instance's host and port
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
                if opt.find('--name=') == 0:
                    name = opt.strip().split('=')[1].strip()
                    config_file = CFG_DIR + 'etcd-' + name + '.conf'
            if os.path.exists(config_file):
                f = open(config_file, 'r')
                cfg_content = f.read()
                f.close()
            for line in cfg_content.split("\n"):
                if line.find('ETCD_LISTEN_CLIENT_URLS=') == 0:
                    address_port = line.split('//')[1].strip('"')
                    address = address_port.split(':')[0]
                    port = address_port.split(':')[1]
                    if address == '0.0.0.0':
                        address = host
                    result.append([address,port,name])
    return result


def get_etcd_data(instance_name=''):
    # etcd cluster health
    pass

if __name__ == "__main__":
    get_etcd_data()
