#!/opt/17173_install/python-2.7.6/bin/python2.7
__author__ = 'Harrison'
from monitor import Monitor
from functools import partial
from argh import ArghParser, arg
import argparse
from mysql_monitor import MySQL_Monitor

# TODO:Completion script comments
BIN = {
    'mysql': 'mysqld',
    'redis': 'redis-server',
    'memcache': 'memcached',
    'mongodb': 'mongod',
}


class ServiceMonitor(Monitor):
    def __init__(self, service, instance=None, cache_path=None):
        app = service + '_' + instance if instance else 'default'
        super(ServiceMonitor, self).__init__(app, cache_path)

    @classmethod
    def _get_bin_name(cls, service):
        return BIN[service]

    def load_data(self, service, instance, item=None, *args):
        """
        auto load func to get monitor data
        @param service: the name of service
        @param instance: string of the instance like ip:port or /dev/sda etc.
        @param is_discovery: is a zabbix low level discovery action
        @param args: other args like the args of func get_XXX_data
        @return: string
        """
        get_func_name = 'get_{}_data'.format(service)
        if hasattr(self, get_func_name):
            #find the func, and add instance as the first arg
            get_func = partial(getattr(self, get_func_name), instance)
            #add args
            if args:
                get_func = partial(get_func, *args)
        else:
            raise AttributeError('have no func named {}'.format(get_func_name))
        return self.get_item(instance=instance, item=item, get_monitor_data_func=get_func)

    def load_keys(self, service, instance, *args):
        """
        auto load func to get monitor data
        @param service: the name of service
        @param instance: string of the instance like ip:port or /dev/sda etc.
        @param is_discovery: is a zabbix low level discovery action
        @param args: other args like the args of func get_XXX_data
        @return: string
        """
        get_func_name = 'get_{}_data'.format(service)
        if hasattr(self, get_func_name):
            #find the func, and add instance as the first arg
            get_func = partial(getattr(self, get_func_name), instance)
            #add args
            if args:
                get_func = partial(get_func, *args)
        else:
            raise AttributeError('have no func named {}'.format(get_func_name))
        keys = self.get_keys(instance=instance, get_monitor_data_func=get_func)
        return keys

    @classmethod
    def discovery(cls, service, macro_name_list, *args):
        discovery_func_name = 'discovery_{}'.format(service)
        if hasattr(ServiceMonitor, discovery_func_name):
            discovery_func = getattr(ServiceMonitor, discovery_func_name)
            if args:
                discovery_func = partial(discovery_func, *args)
        else:
            discovery_func = partial(ServiceMonitor._get_ip_port, ServiceMonitor._get_bin_name(service))
        return ServiceMonitor.get_discovery_data(macro_name_list, discovery_func)

    @classmethod
    def discovery_mysql(cls, *args):
        import os, psutil

        result = []
        for proc in [i for i in psutil.process_iter() if i.name() == 'mysqld']:
            listen = list(sorted([laddr.laddr for laddr in proc.get_connections() if laddr.status == 'LISTEN'])[0])
            if listen[0] == '0.0.0.0' or listen[0] == '::' or listen[0] == '127.0.0.1' or listen[0] == '':
                listen[0] = ServiceMonitor._get_local_ip()
            sock_path = os.path.join(proc.cwd(), 'mysql.sock')
            if MySQL_Monitor.mysql_ping(host=str(listen[0]), port=int(listen[1]), user=args[0], passwd=args[1]) == -1:
                res = MySQL_Monitor.grant_monitor_user(socket=sock_path, user=args[0], host=str(listen[0]),
                                                       passwd=args[1])
            result.append([str(listen[0]), str(listen[1])])
        return result

    def get_mysql_data(self, instance_name='', *args):
        host, port = instance_name.split('/') if instance_name.find('/') != -1 else ('', '')
        user, passwd, socket = ('', '', args[0]) if len(args) == 1 else [args[0], args[1], None] if len(
            args) == 2 else [None, None, None]
        return MySQL_Monitor.get_monitor_data(host=host, port=port, user=user, passwd=passwd, socket=socket)


    def get_memcache_data(self, instance_name):
        """
        the func used to get memcache data
        @param instance_name: the ip:port of memcached instance
        @return: dict
        """
        import memcache

        instance_name = str(instance_name).replace('/', ':')
        conn = memcache.Client([instance_name], debug=0)
        memcached_status = conn.get_stats()[0][1]
        total = int(memcached_status['get_hits']) + int(memcached_status['get_misses'])
        if total:
            x = float(memcached_status['get_hits']) / float(total) * 100
            memcached_status['get_hits_ratio'] = "%.8f" % x
        else:
            memcached_status['get_hits_ratio'] = 0
        return memcached_status


    def get_mongodb_data(self, instance_name, mongo_user, mongo_passwd):
        """
        the func used to get mongodb data
        @param instance_name: the ip:port of mongodb
        @return: dict
        """
        import pymongo

        instance_name = str(instance_name).replace('/', ':')
        uri = "mongodb://{}:{}@{}/admin".format(mongo_user, mongo_passwd, instance_name)
        db = pymongo.MongoClient(uri)
        coll = db.admin
        status = coll.command('serverStatus', 1)
        db.disconnect()
        mongo_status = {}

        mongo_status.update({'host': status['host']})
        mongo_status.update({'version': status['version']})
        mongo_status.update({'uptime': status['uptime']})

        mongo_status.update({'globalLock_activeClients_total': status['globalLock']['activeClients']['total']})
        mongo_status.update({'globalLock_activeClients_readers': status['globalLock']['activeClients']['readers']})
        mongo_status.update({'globalLock_activeClients_writes': status['globalLock']['activeClients']['writers']})

        mongo_status.update({'mem_resident': status['mem']['resident']})
        mongo_status.update({'mem_virtual': status['mem']['virtual']})

        mongo_status.update({'connections_current': status['connections']['current']})
        mongo_status.update({'connections_available': status['connections']['available']})
        mongo_status.update({'connections_totalCreated': status['connections']['totalCreated']})

        mongo_status.update({'indexCounters_hits': status['indexCounters']['hits']})
        mongo_status.update({'indexCounters_misses': status['indexCounters']['misses']})
        mongo_status.update({'indexCounters_missRatio': status['indexCounters']['missRatio']})

        mongo_status.update({'network_bytesIn': status['network']['bytesIn']})
        mongo_status.update({'network_bytesOut': status['network']['bytesOut']})
        mongo_status.update({'network_numRequests': status['network']['numRequests']})

        mongo_status.update({'opcounters_insert': status['opcounters']['insert']})
        mongo_status.update({'opcounters_query': status['opcounters']['query']})
        mongo_status.update({'opcounters_update': status['opcounters']['update']})
        mongo_status.update({'opcounters_delete': status['opcounters']['delete']})
        mongo_status.update({'opcounters_getmore': status['opcounters']['getmore']})

        mongo_status.update({'dur_commits': status['dur']['commits']})
        mongo_status.update({'dur_journaledMB': status['dur']['journaledMB']})
        mongo_status.update({'dur_writeToDataFilesMB': status['dur']['writeToDataFilesMB']})
        mongo_status.update({'dur_timeMs_writerToJournal': status['dur']['timeMs']['writeToJournal']})
        mongo_status.update({'dur_timeMs_writerToDataFiles': status['dur']['timeMs']['writeToDataFiles']})

        for key in mongo_status.keys():
            mongo_status[key.lower()] = mongo_status.pop(key)
        return mongo_status

    @classmethod
    def discovery_redis(cls):
        """
        find redis instance
        @return: [(ip, prot, passwd)]
        """
        import re
        import psutil
        import os

        redises = []
        redis_conf_path_root = '/data'

        for redis_process in [x
                              for x in psutil.process_iter()
                              if len(x.cmdline()) > 0 and re.search(r"redis-server(-\d*)?$",
                                                                    os.path.basename(x.cmdline()[0]))]:
            redis_ip, redis_port = sorted([laddr.laddr
                                           for laddr in redis_process.get_connections()
                                           if laddr.status == 'LISTEN'])[0]
            redis_passwd = ''
            if os.path.isfile(redis_process.cmdline()[1]):
                with open(redis_process.cmdline()[1], 'r') as f:
                    for line in f.readlines():
                        if re.search('^requirepass', line):
                            redis_passwd = line.split()[1]
            else:
                for root_dir, dirs, files in os.walk(redis_conf_path_root):
                    for file in files:
                        if str(file) == 'redis.conf' and re.search(redis_port, str(root_dir)):
                            with open(os.path.join(root_dir, file), 'r') as f:
                                for line in f.read():
                                    if re.search('^requirepass', line):
                                        redis_passwd = line.split()[1]
            redises.append([redis_ip, redis_port, redis_passwd])
        return redises

    def get_redis_data(self, instance_name, *args):
        """
        get monitor data from redis
        @param instance_name: ip:port:passwd
        @return: dict
        """
        import redis

        ip, port, passwd = instance_name.split('/')
        r = redis.StrictRedis(host=ip, port=port, password=passwd)

        return r.info()


@arg('--discovery', '-D', default=False, required=False, help='Discovery the service instance and return json data')
@arg('--service', '-S', required=True, help='the service name of monitor')
@arg('--instance', '-I', help='the name of the instance you want')
@arg('--item', '-K', help='the item of you want')
@arg('--macros', '-M', help='the macro list, used to build discovery data eg:p1,p2,p3')
@arg('--extend', '-E', help='extend args eg. p,p1,p2')
@arg('--cache', '-C', help='cache path')
@arg('--list', '-L', default=False, help='list monitor items for this instance')
def main(args):
    """
    get service monitor data, or discovery service instance
    @param args:
    @return: string when get service data, json when discovery
    """
    if args.discovery:
        assert not args.macros is None, 'must have macros'
    else:
        assert not args.instance is None, 'must have instance'
        #   assert not args.item is None, 'must have item'

    arg_list = []
    if args.extend:
        arg_list = args.extend.split('/')

    if args.discovery:
        print ServiceMonitor.discovery(args.service, args.macros.split('/'), *arg_list)
    else:
        monitor = ServiceMonitor(args.service, cache_path=args.cache if args.cache else None)
        if args.item:
            print monitor.load_data(args.service, args.instance, args.item, *arg_list)
        if args.list:
            print "Monitor Items (in %s)" % args.instance
            for it in monitor.load_keys(args.service, args.instance, *arg_list):
                print it


if __name__ == '__main__':
    parser = ArghParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.set_default_command(main)
    parser.dispatch()
