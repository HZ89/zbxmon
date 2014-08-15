__author__ = 'Harrison'
from Monitor import Monitor
from functools import partial
import netifaces
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

    def _get_ifaddr_list(self):
        addrs=[]
        for iface in netifaces.interfaces():
            if iface.startswith('lo'): continue
            try:
                iaddrs=netifaces.ifaddresses(iface)[netifaces.AF_INET]
            except:
                continue
            for addr in iaddrs:
                addrs.append(addr['addr'])
        return sorted(list(set(addrs)))
    def discovery_zabbix_agent(self):
        service_name='zabbix_agentd'
        services=[]
        for proc in [i for i in psutil.process_iter() if i.name() == service_name]:
            listen=sorted([ laddr.laddr for laddr in proc.get_connection() if laddr.status == 'LISTEN'])[0]
            if listen[0]  in ('0.0.0.0','::'):
                listen[0]=[i for i in self._get_ifaddr_list() if i.startswitch('10.')][0]
    def discovery_mysql(self):
        service_name='mysqld'
        services=[]
        for proc in [i for i in psutil.process_iter() if i.name() == service_name]:
            listen=sorted([ laddr.laddr for laddr in proc.get_connection() if laddr.status == 'LISTEN'])[0]
            if listen[0]  in ('0.0.0.0','::'):
                listen[0]=self.discovery_zabbix_agent()[0]
    def get_mysql_data(self,bind,port,item):
        import MySQLdb
        status_cmds={'SHOW /*!50002 GLOBAL */ STATUS':None,
                     'SHOW VARIABLES':None,
                     'SHOW SLAVE STATUS NOLOCK':None,
                     'SHOW SLAVE STATUS':None,
                     'SHOW MASTER LOGS':None,
                     'SHOW PROCESSLIST':None,
                     'SHOW ENGINES':None
                     }