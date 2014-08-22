__author__ = 'Harrison'
from Monitor import Monitor
from functools import partial
from argh import ArghParser, arg
import argparse

BIN={
    'mysql': 'mysqld',
    'redis-server': 'redis',
    'memcache': 'memcached',
    'mongodb': 'mongod',
}

class ServiceMonitor(Monitor):
    def _get_bin_name(self, service):
        return BIN[service]

    def load_data(self, service, instance, is_discovery=False, item=None ,macro_name_list=None, *args):
        """
        auto load func to get monitor data
        @param service: the name of service
        @param instance: string of the instance like ip:port or /dev/sda etc.
        @param is_discovery: is a zabbix low level discovery action
        @param args: other args like the args of func get_XXX_data
        @return: string
        """

        get_func_name = 'get_{}_data'.format(service)
        discovery_func_name = 'discovery_{}'.format(service)
        if hasattr(self, get_func_name):
            get_func = getattr(self, get_func_name)
            #add args
            if args:
                for tag in args:
                    get_func = partial(get_func, tag)
        else:
            raise AttributeError('have no func named {}'.format(get_func_name))
        if hasattr(self, discovery_func_name):
            discovery_func = getattr(self, discovery_func_name)
        else:
            discovery_func = partial(self._get_ip_port, self._get_bin_name(service))

        if is_discovery:
            return self.get_discovery_data(macro_name_list, discovery_func)
        else:
            return self.get_item(instance=instance, item=item, get_monitor_data_func=get_func)


    def get_memcache_data(self, instance_name):
        """
        the func used to get memcache data
        @param instance_name: the ip:port of memcached instance
        @return: dict
        """
        import memcache
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
        :param instance_name: the ip:port of mongodb
        :param return: dict
        """
        import pymongo
        uri = "mongodb://{}@{}:{}/admin".format(instance_name, mongo_user, mongo_passwd)
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

        return mongo_status

    def discovery_redis(self):
        return None





@arg('--discovery', '-D', default=False, required=True, help='Discovery the service instance and return json data')
@arg('--service', '-S', required=True, help='the service name of monitor')
@arg('--instance', '-I', help='the name of the instance you want')
@arg('--item', '-K', help='the item of you want')
@arg('--macros', '-M', help='the macro list, used to build discovery data')
@arg('--extend', '-E', help='extend args eg. p,p1,p2')
def main(args):
    """

    @param args:
    @return: string
    """
    if args.discovery:
        assert not args.macros is None, 'must have macros'
    else:
        assert not args.instance is None, 'must have instance'
        assert not args.item is None, 'must have item'
    monitor = ServiceMonitor(args.service)
    arg_list = []
    if args.extend:
        assert args.extend.find(',') == 1, "extend must split by ','"
        arg_list = args.extend.split(',')
    print monitor.load_data(args.service, args.instance, args.discovery, args.item, args.macros, *arg_list)




if __name__ == '__main__':

    parser = ArghParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.set_default_command(main)
    parser.dispatch()
