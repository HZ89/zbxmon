# -*- coding: utf8 -*-
__author__ = 'Harrison'

import json
import fcntl
import os
import hashlib
import time
import psutil
import types
from netifaces import interfaces, ifaddresses, AF_INET
from functools import partial
from fcntl import LOCK_EX, LOCK_UN
from re import search



class Monitor(object):
    def __init__(self, app,cache_path=None):

        """
        @param app: type of str, name of your monitor app
        @return: object of Monitor
        """

        self._data = {'file_info': {'file': 'default'}}
        self._app = app
        self._result = {'data': []}
        self._fs = ':'
        self._cache_file_path = os.path.join(cache_path if cache_path and os.path.exists(cache_path) else os.getenv('TMPDIR', '/tmp'),
                                             hashlib.md5(os.uname()[1] + self._app).hexdigest() + '_monitor.tmp')
        self.local_ip=self._get_local_ip()


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

    def _get_local_ip(cls):
        #look for the local private ip
        addresses = []
        for iface_name in interfaces():
            addresses.append([i['addr'] for i in
                              ifaddresses(iface_name).setdefault(AF_INET, [{'addr': 'NO IP addr'}])][0])
        local_ip='0.0.0.0'
        for ips in sorted(addresses):
            if search('^(?:10|172|192)\.'
                      '(?:(?<=192\.)168|(?<=172\.)(?:(?:1[6-9])|(?:2\d)|(?:3[0-1]))|'
                      '(?:(?<=10\.)(?:(?:25[0-5])|(?:2[0-5]\d)|(?:1?\d{1,2}))))\.'
                      '(?:(?:25[0-5])|(?:2[0-5]\d)|(?:1?\d{1,2}))\.'
                      '(?:(?:25[0-5])|(?:2[0-5]\d)|(?:1?\d{1,2}))$',
                ips):
                local_ip = ips
                break
        return  local_ip
    def __del__(self):
        """
        use to free the lock
        @return: None
        """
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
        """
        test cache file exist and have data
        @return: bool
        """

        if os.path.isfile(self._cache_file_path) and len(self._data.keys()) > 1:
            return True

        return False

    def _get_instance_list_from_cache(self):
        """
        get instance list from cache
        @return: list
        """
        return self._data['discovery']
#       return  [ x.split(self._fs) for x in self._data.keys() if x != 'file_info' ]


    def get_item(self, instance, item, get_monitor_data_func=None):
        """
        get item data from instance
        @param instance: the instance you want get data
        @param item: which monitor item you want get from the instance
        @param get_monitor_data_func: this func used for get monitor data from each instances
        @return:
        """

        if get_monitor_data_func:
            assert hasattr(get_monitor_data_func, '__call__'), 'get_monitor_data must can be callable'
        else:
            get_monitor_data_func = self._get_instance_info()

        if self._is_cache_exist():
#            instance_list = [ self._fs.join([i[0], i[1]]) for i in self._get_instance_list() ]
            key = instance + '_' + item
            if self._data['file_info']['file'] == self._data['file_info'][key]:
                monitor_data = {}
#                for instance_name in instance_list:
                monitor_data[instance] = get_monitor_data_func(instance)
                self._make_cache(monitor_data, instance, item)
                return monitor_data[instance][item]
            else:
                #update key version
                self._data['file_info'][key] = self._data['file_info']['file']
                self._cache_file.seek(0)
                self._cache_file.truncate()
                self._cache_file.write(json.dumps(self._data))
                self._cache_file.flush()
                return self._data[instance][item]
        else:
            monitor_data = {}
            monitor_data[instance] = get_monitor_data_func(instance)
            self._make_cache(monitor_data, instance, item)
            return monitor_data[instance][item]

    def _make_cache(self, data, instance, item):
        """
        create and update cache file
        @param data: the data you want put in cache file, must be a dict
        @param instance: which instance of the data
        @param item: used to build key
        @return: None
        """
        result = data

        version = hashlib.md5(str(time.time())).hexdigest()
        if 'discovery' in result.keys():
            self._data.update(result)
        else:
            try:
                for k in result[instance].keys():
                    key = instance + '_' + k
                    if not key in self._data['file_info']:
                        self._data['file_info'][key] = 'default'
                self._data['file_info']['file'] = self._data['file_info'][instance + '_' + item] = version
                self._data.update(result)
            except (ValueError, TypeError, KeyError):
                raise TypeError("have no key named %s" % k)

        self._cache_file.seek(0)
        self._cache_file.truncate()
        self._cache_file.write(json.dumps(self._data,indent=4,sort_keys=True))
        self._cache_file.flush()

    # def _search_ip_port_from_proc(self):
    #     '''
    #     the default func for getting instances list
    #     @return: list
    #     '''
    #     pid_with_ip_port_list = []
    #     if not isinstance(self._regular, str):
    #         raise ValueError("regular must be a str now is %s" % type(self._regular))
    #     for proc in psutil.process_iter():
    #         try:
    #             if re.search(r"%s" % self._regular, os.path.basename(proc.cmdline()[0])):
    #                 listen = [laddr.laddr for laddr in proc.get_connections() if laddr.status == 'LISTEN']
    #                 for ip, port in listen:
    #                     if ip == '0.0.0.0' or ip == '::' or ip == '':
    #                         ip = self._local_ip
    #                     pid_with_ip_port_list.append([ip, port, proc.pid])
    #         except IndexError:
    #             pass
    #     return pid_with_ip_port_list

    def _get_ip_port(self, service):
        """
        cut ip,port from proc
        @param service: the process name you want
        @return: list
        """

        result = []
        for proc in [ i for i in psutil.process_iter() if i.name() == service ]:
            listen = list(sorted([ laddr.laddr for laddr in proc.get_connections() if laddr.status == 'LISTEN' ])[0])
            if listen[0] == '0.0.0.0' or listen[0] == '::' or listen[0] == '127.0.0.1' or listen[0] == '':
                listen[0] = self.local_ip
            result.append([str(listen[0]), str(listen[1])])
        return result

    def _get_instance_list(self, procname=None, is_discovery=None, discovery_func=None):
        """
        use the func discovery_func get instances
        @param is_discovery: bool
        @param discovery_func: the func how to get instaces
        @param procname: arg for self._get_ip_port
        @return: list
        """
        if not discovery_func:
            get_instance_func = partial(self._get_ip_port, procname)
        else:
            get_instance_func = discovery_func

        if is_discovery or not self._is_cache_exist():
            instance_list = get_instance_func()
        else:
            instance_list = self._get_instance_list_from_cache()
        return instance_list

    def get_discovery_data(self, attribute_name_list, discovery_func=None, procname=None):
        """
        format data to json which Zabbix LLD wanted
        if the number of attribute which get_instance_list return more then attribute_name_list,
        EXTEND# will be the name of this attributes
        @param attribute_name_list: return data's key
        @param discovery_func: func used for finding instance
        @param procname: arg for self._get_ip_port
        @return: json data
        """
        result = {'data': []}

        if discovery_func:
            assert hasattr(discovery_func, '__call__'), 'discovery_func must can be callable'

        data = self._get_instance_list(is_discovery=True, discovery_func=discovery_func, procname=procname)

        self._make_cache({'discovery': data}, 'discovery', 'discovery')

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
        """
        you can overload this func get monitor data
        @return: must be dict key by "ip:port"
        """
        return None
