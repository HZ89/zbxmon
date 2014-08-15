__author__ = 'Harrison'
from Monitor import Monitor
from functools import partial
from argh import ArghParser
import argparse

BIN={
    'mysql': 'mysqld',
    'redis': 'redis',
    'memcache': 'memcached',
    'mongodb': 'mongod',
}

class ServiceMonitor(Monitor):
    def _get_bin_name(self, service):
        return BIN[service]

    def load_data(self, service, instance, is_discovery=False, **kwargs):
        '''
        auto load func to get monitor data
        @param service: the name of service
        @param instance: string of the instance like ip:port or /dev/sda etc.
        @param is_discovery: is a zabbix low level discovery action
        @param kwargs: other args
        @return: string
        '''

        get_func_name = 'get_{}_data'.format(service)
        discovery_func_name = 'discovery_{}'.format(service)
        if hasattr(self, get_func_name):
            get_func = getattr(self, get_func_name)
        else:
            raise AttributeError('have no func named {}'.format(get_func_name))
        if hasattr(self, discovery_func_name):
            discovery_func = getattr(self, discovery_func_name)
        else:
            discovery_func = partial(self._get_ip_port, self._get_bin_name(service))

        if is_discovery:
            return self.get_discovery_data(kwargs['attribute_name_list'], discovery_func)
        else:
            return self.get_item(instance, kwargs['item'], get_monitor_data_func=get_func)