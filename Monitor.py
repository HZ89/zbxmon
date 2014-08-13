#!/opt/17173_install/python-2.7.6/bin/python2.7

# -*- coding: utf8 -*-
__author__ = 'Harrison'

import json
import fcntl
import os
import hashlib
import time
import psutil
import re
import netifaces
import types
from fcntl import LOCK_EX, LOCK_UN



class Monitor(object):
    def __init__(self, app, get_monitor_data=None, instance=None, regular=None, attribute_name_list=None,
                 discovery_func=None, is_discovery=False):

        """
        @param app: type of str, name of your monitor app
        @param get_monitor_data: type of function, the method of how get your app's data, should return a dict
        @param instance: key of data the get_monitor_data return
        @param regular: regular expression used by _search_ip_port_from_proc
        @param attribute_name_list: the name of attribute from discovery_func
        @return: object of Monitor
        """
        self._regular = regular
        self._data = {'file_info': {'file': 'default'}}
        self._app = app
        self._result = {'data': []}
        self._fs = ':'
        self._cache_file_path = os.getenv('TMPDIR', '/tmp') + '/' + hashlib.md5(
            os.uname()[1] + self._app).hexdigest() + '_monitor.tmp'
        interface = netifaces.interfaces()

        if 'eth1' in interface:
            self._local_ip = netifaces.ifaddresses('eth1')[netifaces.AF_INET][0]['addr']
        elif 'em2' in interface:
            self._local_ip = netifaces.ifaddresses('em2')[netifaces.AF_INET][0]['addr']
        else:
            raise SystemError("can not find internal netifaces")
        try:
            self._cache_file = open(self._cache_file_path, "r+")
            fcntl.lockf(self._cache_file.fileno(), LOCK_EX)
            self._data = json.loads(self._cache_file.readline())
        except (IOError, ValueError):
            self._cache_file = open(self._cache_file_path, "w+")
            fcntl.lockf(self._cache_file.fileno(), LOCK_EX)
#            self._cache_file.write(str(json.dumps(self._data)))
#            self._make_cahe()
#            self._cache_file.flush()

    def __del__(self):
        fcntl.lockf(self._cache_file.fileno(), LOCK_UN)
        if not self._cache_file is None:
            self._cache_file.close()

    #def __enter__(self):    # In testing
    #    return self
    #
    #def __exit__(self, exc_type, exc_val, exc_tb):    # In testing
    #    if exc_type is None:
    #        self.__del__()
    #    else:
    #        self.__del__()
    #        print('Have an error', exc_type)
    #        return False

    def _is_cache_exist(self):

        if os.path.isfile(self._cache_file_path) and len(self._data.keys()) > 1:
            return True

        return False

    def _get_instance_list_from_cache(self):
        return self._data['discovery']
#        return  [ x.split(self._fs) for x in self._data.keys() if x != 'file_info' ]


    def get_item(self, instance, item, get_monitor_data_func=None):

        if get_monitor_data_func:
            assert isinstance(get_monitor_data_func, types.FunctionType), 'get_monitor_data must be a function'
        else:
            get_monitor_data_func = self._get_instance_info()

        instance_list = self._get_instance_list()
        key = instance + '_' + item
#        read file in init func
#        if self._data['file_info']['file'] == 'default' and self._cache_file.mode == 'rw':
#            self._data = json.loads(self._cache_file.readline())

        if self._is_cache_exist():
            if self._data['file_info']['file'] == self._data['file_info'][key]:
                self._make_cache(get_monitor_data_func(instance_list), instance)
                return self._data[instance][item]
            else:
                #change version
                self._data['file_info'][key] = self._data['file_info']['file']
                self._cache_file.seek(0)
                self._cache_file.truncate()
                self._cache_file.write(json.dumps(self._data))
                self._cache_file.flush()
                return self._data[instance][item]
        else:
            self._make_cache(get_monitor_data_func(instance_list), instance)
            return self._data[instance][item]

    def _make_cache(self, data, instance):
        result = data
        # if not isinstance(result, dict):
        #     raise TypeError("result must be a dict!")
        version = hashlib.md5(str(time.time())).hexdigest()
        if self._is_cache_exist():
            try:
                for k in result[instance].keys():
                    key = instance + '_' + k
                    if not key in self._data['file_info']:
                        self._data['file_info'][key] = 'default'
                self._data['file_info']['file'] = self._data['file_info'][instance + '_' + self._item] = version
                self._data.update(result)
            except (ValueError, TypeError, KeyError):
                raise TypeError("have no key named %s" % key)
        else:
            self._data.update(result)

        self._cache_file.seek(0)
        self._cache_file.truncate()
        self._cache_file.write(json.dumps(self._data))
        self._cache_file.flush()

    def _search_ip_port_from_proc(self):
        pid_with_ip_port_list = []
        if not isinstance(self._regular, str):
            raise ValueError("regular must be a str now is %s" % type(self._regular))
        for proc in psutil.process_iter():
            try:
                if re.search(r"%s" % self._regular, os.path.basename(proc.cmdline()[0])):
                    listen = [laddr.laddr for laddr in proc.get_connections() if laddr.status == 'LISTEN']
                    for ip, port in listen:
                        if ip == '0.0.0.0' or ip == '::' or ip == '':
                            ip = self._local_ip
                        pid_with_ip_port_list.append([ip, port, proc.pid])
            except IndexError:
                pass
        return pid_with_ip_port_list

    def _get_ip_port(self):
        ip_ports = []
        for ip, port, _ in self._search_ip_port_from_proc():
            ip_ports.append([ip, port])
        return ip_ports

    def _get_instance_list(self, is_discovery=None, discovery_func=None):
        if not discovery_func:
            get_instance_func = self._get_ip_port
        else:
            get_instance_func = discovery_func

        if is_discovery or not self._is_cache_exist():
            instance_list = get_instance_func()
        else:
            instance_list = self._get_instance_list_from_cache()
        return instance_list

    def get_discovery_data(self, attribute_name_list, discovery_func=None):
        '''
        format data to json which Zabbix LLD wanted
        if the number of attribute which get_instance_list return more then attribute_name_list,
        EXTEND# will be the name of this attributes
        @param attribute_name_list: return data's key
        @param discovery_func: func used for finding instance
        @return: json data
        '''
        result = {'data': []}

        if discovery_func:
            assert isinstance(discovery_func, types.FunctionType), 'discovery_func must be a function'

        data = self._get_instance_list(is_discovery=True, discovery_func=discovery_func)

        self._make_cache({'discovery': data}, 'discovery')

        for instance in data:
            tmp_dict = {}
            for attribute_name in attribute_name_list:
                tmp_dict.update({"{#%s}" % attribute_name: instance.pop(0)})
            # if len(instance) > 0:
            #     for extend in instance:
            #         tmp_dict.update({"{#EXTEND%d}" % instance.index(extend): extend})
            result['data'].append(tmp_dict)

        return json.dumps(result)

    def _get_instance_info(self):
        '''
        you can overload this func get monitor data
        @return: must be dict key by "ip:port"
        '''
        return None
