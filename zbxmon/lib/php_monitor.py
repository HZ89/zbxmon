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
import flup_fcgi_client as fcgi_client

BINNAME = 'php-fpm'


def discovery_php(ALL=False, *args):
    '''
    discovery php-fpm instance's host and port
    '''
    fpm_pid_list = []
    fpm_cfg_dict = {}
    fpm_pid = ''
    fpm_cmdline = ''

    for i in psutil.process_iter():
        if i.name() == BINNAME and i.username() == 'root':
            fpm_pid = int(i.pid)
            fpm_cmdline = i.cmdline()

    if fpm_pid and fpm_cmdline:

        if len(fpm_cmdline) > 1:
            fpm_config_file = fpm_cmdline[2]
        elif len(fpm_cmdline) == 1:
            t = fpm_cmdline[0]
            s_index = t.find('(')
            e_index = t.find(')')
            fpm_config_file = t[s_index + 1:e_index]

        f = open(fpm_config_file, 'r')
        master_cfg_content = f.read()
        f.close()

        include_p = re.compile('\ninclude.*', re.I)
        include_m = include_p.search(master_cfg_content)
        if include_m:
            include_file = include_m.group(0)
            include_file = include_file.strip()
            l = include_file.split('/')[1:-1]
            include_dir = '/'
            for i in l:
                include_dir = include_dir + i + '/'

            if include_dir:
                count = 0
                for cfg_file in os.listdir(include_dir):
                    f = open(include_dir + cfg_file, 'r')
                    single_cfg_content = f.read()
                    f.close()
                    single_p = re.compile('\npm\.status_path.*', re.I)
                    single_m = single_p.search(single_cfg_content)
                    single_ping_p = re.compile('\nping\.path.*', re.I)
                    single_ping_m = single_ping_p.search(single_cfg_content)
                    single_pong_p = re.compile('\nping\.response.*', re.I)
                    single_pong_m = single_pong_p.search(single_cfg_content)

                    if single_m:
                        status_path = single_m.group(0)
                        status_path = status_path.strip()
                        status_path = str(status_path.split('=')[-1]).strip()

                        if status_path:
                            single_p = re.compile('\nlisten.*', re.I)
                            single_m = single_p.search(single_cfg_content)

                            if single_m:
                                listen = single_m.group(0)
                                listen = listen.strip()
                                listen = listen.split('=')[1].strip()

                                if listen:
                                    if re.search("^(\d+\.){3}\d+:\d+$", listen):
                                        ip = listen.split(':')[0]
                                        port = listen.split(':')[1]
                                        fpm_cfg_dict[count] = {}
                                        fpm_cfg_dict[count]['ip'] = ip
                                        fpm_cfg_dict[count]['port'] = port
                                        fpm_cfg_dict[count]['status_path'] = status_path
                                    else:
                                        fpm_cfg_dict[count] = {}
                                        fpm_cfg_dict[count]['status_path'] = status_path
                                        fpm_cfg_dict[count]['socket'] = listen

                    if single_ping_m:
                        ping_path = single_ping_m.group(0)
                        ping_path = ping_path.strip()
                        ping_path = str(ping_path.split('=')[-1]).strip()

                        if ping_path:
                            fpm_cfg_dict[count]['ping_path'] = ping_path

                    if single_pong_m:
                        pong_path = single_pong_m.group(0)
                        pong_path = pong_path.strip()
                        pong_path = str(pong_path.split('=')[-1]).strip()

                        if pong_path:
                            fpm_cfg_dict[count]['pong_path'] = pong_path

                    count += 1
        else:
            fpm_cfg_dict[0] = {}
            master_p = re.compile('\npm\.status_path.*', re.I)
            master_m = master_p.search(master_cfg_content)

            if master_m:
                status_path = master_m.group(0)
                status_path = status_path.strip()
                status_path = str(status_path.split('=')[-1]).strip()

                if status_path:
                    master_p = re.compile('\nlisten.*:\d+', re.I)
                    master_m = master_p.search(master_cfg_content)
                    if master_m:
                        listen = master_m.group(0)
                        listen = listen.strip()
                        listen = listen.split('=')[1].strip()
                        if listen:
                            p = re.compile('')
                            if re.search("^(\d+\.){3}\d+:\d+$", listen):
                                ip = listen.split(':')[0]
                                port = listen.split(':')[1]
                                fpm_cfg_dict[0]['ip'] = ip
                                fpm_cfg_dict[0]['port'] = port
                                fpm_cfg_dict[0]['status_path'] = status_path
                            else:
                                fpm_cfg_dict[0]['status_path'] = status_path
                                fpm_cfg_dict[0]['socket'] = listen

            master_ping_p = re.compile('\nping\.path.*', re.I)
            master_ping_m = master_ping_p.search(master_cfg_content)

            if master_ping_m:
                ping_path = master_ping_m.group(0)
                ping_path = ping_path.strip()
                ping_path = str(ping_path.split('=')[-1]).strip()

                if ping_path:
                    fpm_cfg_dict[0]['ping_path'] = ping_path

            master_pong_p = re.compile('\nping\.response.*', re.I)
            master_pong_m = master_pong_p.search(master_cfg_content)

            if master_pong_m:
                pong_path = master_pong_m.group(0)
                pong_path = pong_path.strip()
                pong_path = str(pong_path.split('=')[-1]).strip()

                if pong_path:
                    fpm_cfg_dict[0]['pong_path'] = pong_path

    # print fpm_cfg_dict
    # {0: {'status_path': '/status', 'socket': '/dev/shm/php-fpm.socket'}, 1: {'ip': '127.0.0.1', 'status_path': '/status', 'port': '9001'}}
    result = []
    for i in fpm_cfg_dict.keys():
        if len(fpm_cfg_dict[i]) == 5:
            result.append([fpm_cfg_dict[i]['ip'], fpm_cfg_dict[i]['port']])
        if len(fpm_cfg_dict[i]) == 4:
            result.append(['127.0.0.1', fpm_cfg_dict[i]['socket']])
    if ALL == False:
        return result
    elif ALL == True:
        return fpm_cfg_dict


def get_php_data(instance_name='', *args):
    """
    get monitor data from nginx
    @param instance_name: 'http://ip:port/nginx-status active'
    @return: dict
    """
    # /app/bin/zbxmon --service nginx --item reading --instance 10.10.60.211/8888
    if len(instance_name.split('/')) == 2:
        instance_ip = instance_name.split('/')[0]
        instance_port = instance_name.split('/')[1]
    elif len(instance_name.split('/')) > 2:
        instance_ip = instance_name.split('/')[0]
        instance_port = '/'
        for i in instance_name.split('/')[1:]:
            if i:
                instance_port += i + '/'
        instance_port = instance_port.rstrip('/')
    host_info = discovery_php(ALL=True)
    # print host_info
    # {0: {'pong_path': 'pong', 'ping_path': '/ping', 'status_path': '/status', 'socket': '/dev/shm/php-fpm.socket'}}
    for i in host_info.keys():
        if len(host_info[i]) == 5:
            if instance_ip == host_info[i]['ip'] and instance_port == host_info[i]['port']:
                status_path = host_info[i]['status_path']
                ping_path = host_info[i]['ping_path']
                pong_path = host_info[i]['pong_path']
                fcgi = fcgi_client.FCGIApp(host=host_info[i]['ip'], port=host_info[i]['port'])
                env = {
                    'SCRIPT_NAME': status_path,
                    'SCRIPT_FILENAME': status_path,
                    'QUERY_STRING': 'json',
                    'REQUEST_METHOD': 'GET'
                }
                alive_env = {
                    'SCRIPT_NAME': ping_path,
                    'SCRIPT_FILENAME': ping_path,
                    'QUERY_STRING': 'json',
                    'REQUEST_METHOD': 'GET'
                }
        if len(host_info[i]) == 4:
            if instance_port == host_info[i]['socket']:
                status_path = host_info[i]['status_path']
                ping_path = host_info[i]['ping_path']
                pong_path = host_info[i]['pong_path']
                fcgi = fcgi_client.FCGIApp(connect=host_info[i]['socket'])
                env = {
                    'SCRIPT_NAME': status_path,
                    'SCRIPT_FILENAME': status_path,
                    'QUERY_STRING': 'json',
                    'REQUEST_METHOD': 'GET'
                }
                alive_env = {
                    'SCRIPT_NAME': ping_path,
                    'SCRIPT_FILENAME': ping_path,
                    'QUERY_STRING': 'json',
                    'REQUEST_METHOD': 'GET'
                }

    code, headers, out, err = fcgi(env)
    out = out.lstrip('{').rstrip('}')
    l_out = out.split(',')
    d_out = {}
    for i in l_out:
        d_out[i.split(':')[0].strip('"')] = i.split(':')[1].strip('"')

    alive_code, alive_headers, alive_out, alive_err = fcgi(alive_env)
    alive_out = alive_out.lstrip('{').rstrip('}').strip()

    # {"pool":"www","process manager":"dynamic","start time":1447740439,"start since":13513,"accepted conn":17,"listen queue":0,"max listen queue":0,"listen queue len":0,"idle processes":4,"active processes":1,"total processes":5,"max active processes":1,"max children reached":0,"slow requests":0}
    result = {}
    if "start since" in d_out:
        result['start_since'] = int(d_out["start since"])
    if "accepted conn" in d_out:
        result['accepted_conn'] = int(d_out["accepted conn"])
    if "listen queue" in d_out:
        result['listen_queue'] = int(d_out["listen queue"])
    if "max listen queue" in d_out:
        result['max_listen_queue'] = int(d_out["max listen queue"])
    if "listen queue len" in d_out:
        result['listen_queue_len'] = int(d_out["listen queue len"])
    if "idle processes" in d_out:
        result['idle_processes'] = int(d_out["idle processes"])
    if "active processes" in d_out:
        result['active_processes'] = int(d_out["active processes"])
    if "total processes" in d_out:
        result['total_processes'] = int(d_out["total processes"])
    if "max active processes" in d_out:
        result['max_active_processes'] = int(d_out["max active processes"])
    if "max children reached" in d_out:
        result['max_children_reached'] = int(d_out["max children reached"])
    if "slow requests" in d_out:
        result['slow_requests'] = int(d_out["slow requests"])
    if alive_out == pong_path:
        result['alive'] = 'up'
    else:
        result['alive'] = 'down'

    return result


if __name__ == "__main__":
    get_php_data()
