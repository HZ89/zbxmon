#!/app/bin/python2.7
# -*- coding: utf8 -*-
__author__ = 'gaobiling'
__verion__ = '0.5.0'
import os
import sys
import string
import json
import re
import traceback
import psutil
import netifaces
import urllib
from zbxmon.monitor import Monitor

BINNAME = 'nginx'

def discovery_nginx(status_path=False):
    '''
    discovery nginx instance's host and port
    '''
    nginx_pid = ''
    instance_list=[]
    for i in psutil.process_iter():
        if i.name() == BINNAME and i.username() == 'root':
            nginx_pid = i.pid
    
    nginx_proc_file = '/proc/{0}/cmdline'.format(nginx_pid)

    if os.path.exists(nginx_proc_file):
        f = open(nginx_proc_file, 'r')
        nginx_cmd = f.read()
        f.close()
        nginx_cfg_file = nginx_cmd.strip().split()[-1]

        f = open(nginx_cfg_file, 'r')
        cfg_content = f.read()
        f.close()

#        print cfg_content
        p_status_on = re.compile('stub_status\s+on;', re.I)
        m_status_on = p_status_on.search(cfg_content)
        if m_status_on:
            p_path = re.compile('location.*', re.I)
            m_path = p_path.search(cfg_content)
            if m_path:
                path = m_path.group(0).strip().split()[1]
            p_port = re.compile('listen\s+.*', re.I)
            m_port = p_port.search(cfg_content)
            if m_port:
                l_port = m_port.group(0).strip().strip(';').split()[-1].split(':')
                if(len(l_port)==2):
                    port = l_port[1]
                else:
                    port = l_port[0]
            ip = Monitor.get_local_ip()

    result = []
    if not status_path:
        result.append([str(ip),str(port)])
        return result
    else:
        return path

def get_nginx_data(instance_name='', *args):
    """
    get monitor data from nginx
    @param instance_name: 'http://ip:port/nginx-status active'
    @return: dict
    """
    path = discovery_nginx(status_path=True)
    ip = instance_name.strip().split('/')[0]
    port = instance_name.strip().split('/')[1]
    

    default_url = 'http://{0}:{1}{2}'.format(ip, port, path)
    f = urllib.urlopen(default_url)

    nginx_status_contents = f.read()
    
    for line in nginx_status_contents.split("\n"):
        regx_obj = re.search(r"^Active\s+connections:\s+(\d+).*$", line, re.U)
        if regx_obj:
            active = regx_obj.groups()[0]
            continue
        regx_obj = re.search(r"^server\s+accepts\s+handled\s+requests.*$", line, re.U)
        if regx_obj:
            continue
        regx_obj = re.search(r"^\s+(\d+)\s+(\d+)\s+(\d+).*$", line, re.U)
        if regx_obj:
            accepts, handled, requests = regx_obj.groups()
            continue
        regx_obj = re.search(r"^Reading:\s+(\d+)\s+Writing:\s+(\d+)\s+Waiting:\s+(\d+).*$", line, re.U)
        if regx_obj:
            reading, writing, waiting = regx_obj.groups()

    result = {
        'active': int(active),
        'accepts': int(accepts),
        'handled': int(handled),
        'requests': int(requests),
        'reading': int(reading),
        'writing': int(writing),
        'waiting': int(waiting)
    }

    return result


if __name__ == "__main__":
    get_nginx_data()
