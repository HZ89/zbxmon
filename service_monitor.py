#!/opt/17173_install/python-2.7.6/bin/python2.7
# coding:utf-8
__author__ = 'Harrison'

import os
import sys

sys.path.extend(os.path.realpath(__file__))

from monitor import Monitor
from functools import partial
from argh import ArghParser, arg
import argparse
from lib.mysql_monitor import MySQL_Monitor

# TODO:Completion script comments


class ServiceMonitor(Monitor):
    def __init__(self, service, instance=None, cache_path=None):
        app = service + '_' + instance if instance else 'default'
        super(ServiceMonitor, self).__init__(app, cache_path)

    @classmethod
    def _get_bin_name(cls, service):
        BIN = {
            'mysql': 'mysqld',
            'redis': 'redis-server',
            'memcache': 'memcached',
            'mongodb': 'mongod',
        }
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
            # find the func, and add instance as the first arg
            get_func = partial(getattr(self, get_func_name), instance)
            # add args
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
            # find the func, and add instance as the first arg
            get_func = partial(getattr(self, get_func_name), instance)
            # add args
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


    # @classmethod
    # def discovery_phpfpm(cls, *args):
    # """
    # find local php-fpm process from config files
    # @param args: first value is config dir root, second value is regular used for find php-fpm config file
    #     @return:
    #     """
    #     import ConfigParser
    #     config_path = args[0]
    #     prog = re.compile(args[1])
    #     fpm_conf = []
    #     if os.path.isdir(config_path):
    #         for root_dir, dirs, files in os.walk(config_path):
    #             for file in files:
    #                 if prog.match(file):
    #                     config = ConfigParser.RawConfigParser()
    #                     config.read(file)
    #                     for section in config.sections():
    #                         if section == 'global':
    #                             continue
    #                         pool = {}
    #                         for item, value in config.items(section):




    @classmethod
    def discovery_mysql(cls, *args):
        import psutil

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
        status = None
        try:
            conn = memcache.Client([instance_name], debug=0)
            status = conn.get_stats()[0][1]
        except Exception as e:
            status = {}
        check_keys = {
            #
            'pid': int,  # memcache服务器进程ID
            'uptime': int,  # 服务器已运行秒数
            'time': int,  # 服务器当前Unix时间戳
            'version': str,  # memcache版本
            'pointer_size': int,  # 操作系统指针大小
            'libevent': str,  # libevent版本
            # cpu
            'rusage_user': float,  # 进程累计用户时间
            'rusage_system': float,  # 进程累计系统时间
            # connections
            'accepting_conns': int,  # 服务器是否达到过最大连接（0/1）
            'curr_connections': int,  # 当前连接数量
            'threads': int,  # 当前线程数
            'listen_disabled_num': int,  # 失效的监听数
            'conn_yields': int,  # 连接操作主动放弃数目: int,内部请求数达到0
            #
            'total_connections': int,  # Memcached运行以来连接总数
            'connection_structures': int,  # Memcached分配的连接结构数量

            # count
            'cmd_set': int,  # set命令请求次数
            'cmd_get': int,  # get命令请求次数
            'cas_badval': int,  # 使用擦拭次数
            'cmd_touch': int,  # 执行touch次数，touch可以刷新过期时间
            'cmd_flush': int,  # flush命令请求次数
            'auth_cmds': int,  # 认证命令处理的次数
            'auth_errors': int,  # 认证失败数目
            # ratio
            'get_hits': int,  # get命令命中次数
            'get_misses': int,  # get命令未命中次数

            'delete_misses': int,  # delete命令未命中次数
            'delete_hits': int,  # delete命令命中次数

            'incr_misses': int,  # incr命令未命中次数
            'incr_hits': int,  # incr命令命中次数

            'decr_misses': int,  # decr命令未命中次数
            'decr_hits': int,  # decr命令命中次数

            'cas_misses': int,  # cas命令未命中次数
            'cas_hits': int,  # cas命令命中次数

            'touch_hits': int,  # touch命中次数
            'touch_misses': int,  # touch未命中次数
            # access
            'bytes_read': int,  # 读取总字节数
            'bytes_written': int,  # 发送总字节数
            # memory
            'limit_maxbytes': int,  # 分配的内存总大小（字节）
            'bytes': int,  # 当前存储占用的字节数
            'hash_bytes': int,  # hash 内存使用总量单位为byte
            # item
            'curr_items': int,  # 当前存储的数据总数
            'total_items': int,  # 启动以来存储的数据总数
            'evictions': int,  # LRU释放的对象数目
            'reclaimed': int,  # 已过期的数据条目来存储新数据的数目
        }
        result = {}
        for ckey in check_keys.keys():
            result[ckey] = check_keys[ckey](status[ckey] if status.has_key(ckey) else '0');

        hits_ratio_cmds = ['get', 'delete', 'incr', 'decr', 'cas', 'touch']
        for cmd in hits_ratio_cmds:
            hit_key = "%s_hits" % cmd
            miss_key = "%s_misses" % cmd
            if result.has_key(hit_key) and result.has_key(miss_key) \
                    and result[hit_key] + result[miss_key] > 0:
                result["%s_hists_ratio" % cmd] = int(result[hit_key] / (result[hit_key] + result[miss_key]) * 100)
            else:
                result["%s_hists_ratio" % cmd] = 0

        return result


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

        mongo_status.update({'host': status.get('host', ''),
                             'version': status.get('version', ''),
                             'uptime': status.get('uptime', 0),
                             # global lock
                             'globalLock_activeClients_total': status.get('globalLock', {}).get('activeClients',
                                 {}).get('total', 0),
                             'globalLock_activeClients_readers': status.get('globalLock', {}).get('activeClients',
                                 {}).get('readers', 0),
                             'globalLock_activeClients_writers': status.get('globalLock', {}).get('activeClients',
                                 {}).get('writers', 0),
                             'globalLock_currentQueue_total': status.get('globalLock', {}).get('currentQueue', {}).get(
                                 'total', 0),
                             'globalLock_currentQueue_readers': status.get('globalLock', {}).get('currentQueue',
                                 {}).get('readers', 0),
                             'globalLock_currentQueue_writers': status.get('globalLock', {}).get('currentQueue',
                                 {}).get('writers', 0),
                             #'globalLock_ratio': status.get('globalLock',{}).get('ratio',{}),
                             # memory
                             'mem_resident': status.get('mem', {}).get('resident', 0) * 1024 * 1024,
                             'mem_virtual': status.get('mem', {}).get('virtual', 0) * 1024 * 1024,
                             'mem_mapped': status.get('mem', {}).get('mapped', 0) * 1024 * 1024,
                             'mem_mappedWithJournal': status.get('mem', {}).get('mappedWithJournal', 0) * 1024 * 1024,
                             'mem_extra_heap_usage_bytes': status.get('extra_info', {}).get('heap_usage_bytes', 0),
                             'mem_extra_page_faults': status.get('extra_info', {}).get('page_faults', 0),
                             # connections
                             'connections_current': status.get('connections', {}).get('current', 0),
                             'connections_available': status.get('connections', {}).get('available', 0),
                             'connections_total': status.get('connections', {}).get('current', {}) + status.get(
                                 'connections', {}).get('available', 0),
                             'connections_totalCreated': status.get('connections', {}).get('totalCreated', 0),
                             # index
                             'index_accesses': status.get('indexCounters', {}).get('accesses', 0),
                             'index_hits': status.get('indexCounters', {}).get('hits', 0),
                             'index_misses': status.get('indexCounters', {}).get('misses', 0),
                             'index_missRatio': status.get('indexCounters', {}).get('missRatio', 0),
                             'index_resets': status.get('indexCounters', {}).get('resets', 0),
                             # network
                             'network_bytesIn': status.get('network', {}).get('bytesIn', 0),
                             'network_bytesOut': status.get('network', {}).get('bytesOut', 0),
                             'network_numRequests': status.get('network', {}).get('numRequests', 0),
                             # operations
                             'opcounters_insert': status.get('opcounters', {}).get('insert', 0),
                             'opcounters_query': status.get('opcounters', {}).get('query', 0),
                             'opcounters_update': status.get('opcounters', {}).get('update', 0),
                             'opcounters_delete': status.get('opcounters', {}).get('delete', 0),
                             'opcounters_getmore': status.get('opcounters', {}).get('getmore', 0),
                             # dur
                             'dur_commits': status.get('dur', {}).get('commits', 0),
                             'dur_journaledMB': status.get('dur', {}).get('journaledMB', 0) * 1024 * 1024,
                             'dur_writeToDataFilesMB': status.get('dur', {}).get('writeToDataFilesMB', 0) * 1024 * 1024,
                             'dur_timeMs_writerToJournal': status.get('dur', {}).get('timeMs', {}).get('writeToJournal',
                                                                                                       0),
                             'dur_timeMs_writerToDataFiles': status.get('dur', {}).get('timeMs', {}).get(
                                 'writeToDataFiles', 0),
                             # repl
                             'repl_ismaster': status.get('repl', {}).get('ismaster', 0),
                             # io flush
                             'backFlush_flushes': status.get('backgroundFlushing', {}).get('flushes', 0),
                             'backFlush_total_ms': status.get('backgroundFlushing', {}).get('total_ms', 0),
                             'backFlush_average_ms': status.get('backgroundFlushing', {}).get('average_ms', 0),
                             'backFlush_last_ms': status.get('backgroundFlushing', {}).get('last_ms', 0),
                             # cluster
                             # cursors
                             'cursors_totalOpen': status.get('cursors', {}).get('totalOpen', 0),
                             'cursors_timedOut': status.get('cursors', {}).get('timedOut', 0),
                             # asserts
                             'asserts_msg': status.get('asserts', {}).get('msg', 0),
                             'asserts_regular': status.get('asserts', {}).get('regular', 0),
                             'asserts_warning': status.get('asserts', {}).get('warning', 0),
                             'asserts_user': status.get('asserts', {}).get('user', 0),
                             'asserts_rollovers': status.get('asserts', {}).get('rollovers', 0)
        })

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

        redises = []
        redis_conf_path_root = '/data'
        redis_conf_file_name = 'redis.conf'

        for redis_process in [x
                              for x in psutil.process_iter()
                              if len(x.cmdline()) > 0 and os.path.basename(x.exe()) == 'redis-server']:
            try:
                redis_ip, redis_port = sorted([laddr.laddr
                                               for laddr in redis_process.get_connections()
                                               if laddr.status == 'LISTEN'])[0]
            except:
                continue
            redis_passwd = ''
            config_files = []
            if os.path.isdir(redis_process.getcwd()):
                config_files.append(redis_process.getcwd() + redis_conf_file_name)
            elif len(redis_process.cmdline()) > 1 and os.path.isfile(redis_process.cmdline()[1]):
                config_files.append(redis_process.cmdline()[1])
            else:
                for root_dir, dirs, files in os.walk(redis_conf_path_root):
                    if 'redis.conf' in files:
                        config_files.append(os.path.join(root_dir, redis_conf_file_name))

            for config_file in config_files:
                with open(config_file, 'r') as f:
                    passwd = None
                    port = None
                    for line in f.readlines():
                        if re.search('^requirepass', line):
                            passwd = line.split()[1]
                        if re.search('^port', line):
                            port = line.split()[1]
                if passwd and port and str(redis_port) == port:
                    redis_passwd = str(passwd)
                    break
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
        d = r.info()
        check_items = {
            'redis_version': str,
            'redis_mode': str,
            'uptime_in_seconds': int,
            # Clients
            'connected_clients': int,  # 当前客户端连接数
            'blocked_clients': int,  # 正在等待阻塞命令（BLPOP、BRPOP、BRPOPLPUSH）的客户端的数量
            'connected_slaves': int,  # 当前从连接的数量
            'rejected_connections': int,
            'total_connections_received': int,  # 运行以来连接过的客户端的总数量
            'client_longest_output_list': int,  # 当前连接的客户端当中，最长的输出列表
            'client_biggest_input_buf': int,  # 当前连接的客户端当中，最大输入缓存
            # Memory
            'used_memory': int,  # 由redis分配器分配的内存总量，以字节（byte）为单位
            'used_memory_rss': int,  # 从操作系统的角度，返回rRedis已分配的内存总量（俗称常驻集大小),这个值和top、ps等命令的输出一致。
            'used_memory_peak': int,  # redis的内存消耗峰值（以字节为单位）
            'used_memory_lua': int,  # 引擎所使用的内存大小（以字节为单位）
            'mem_fragmentation_ratio': float,  # 内存碎片比率:userd_memory_rss和used_memory之间的比率


            # Persistence
            'rdb_changes_since_last_save': int,  # 上次保存数据库之后，执行命令的次数
            'rdb_bgsave_in_progress': int,  # 后台进行中的save操作的数量
            'rdb_last_save_time': int,  # 最后一次成功保存的时间点，以 UNIX 时间戳格式显示
            'rdb_last_bgsave_status': str,
            'rdb_last_bgsave_time_sec': int,
            'rdb_current_bgsave_time_sec': int,


            # Stats
            'total_commands_processed': int,  # 运行以来执行过的命令的总数量
            'instantaneous_ops_per_sec': int,  # 每秒瞬间ops数
            'expired_keys': int,  # 运行以来过期的 key 的数量
            'evicted_keys': int,  # 运行以来删除过的key的数量
            'keyspace_hits': int,  # 命中 key 的次数
            'keyspace_misses': int,  # 不命中 key 的次数
            'pubsub_channels': int,  # 当前使用中的频道数量
            'pubsub_patterns': int,  # 当前使用的模式的数量
            #'latest_fork_usec':int,

            # Replication
            'role': str,  # 当前实例的角色master还是slave
            'master_host': str,
            'master_port': int,
            'master_link_status': str,  # up or down
            'master_last_io_seconds_ago': int,
            'master_sync_in_progress': int,
            'slave_lists': str,

            #'slave0:ip=192.168.200.25,port=62710,state=online,offset=823669419,lag=1     #offset 当前从的数据偏移量位置

            # CPU
            'used_cpu_sys': float,
            'used_cpu_user': float,
            'used_cpu_sys_children': float,
            'used_cpu_user_children': float,
        }
        redis_stats = {k: d[k] if d.has_key(k) else v() for k, v in check_items.iteritems()}
        if redis_stats['connected_slaves'] > 0:
            slave_lists = set()
            for i in range(redis_stats['connected_slaves']):
                if d.has_key("slave%s" % i):
                    slave_lists.add(str(d["slave%s" % i]))
            redis_stats['slave_lists'] = ','.join(list(slave_lists))
        return redis_stats


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
        # assert not args.item is None, 'must have item'

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
            for it in sorted(monitor.load_keys(args.service, args.instance, *arg_list)):
                print it


if __name__ == '__main__':
    parser = ArghParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.set_default_command(main)
    parser.dispatch()
