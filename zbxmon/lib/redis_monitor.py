# -*- coding: utf8 -*-
__author__ = 'Harrison'

import os,sys
import redis
import re
import psutil

BINNAME = 'redis-server'

def discovery_redis():
    """
    find redis instance
    @return: [(ip, prot, passwd)]
    """

    redises = []
    redis_conf_path_root = '/data'
    redis_conf_file_name = 'redis.conf'
    for redis_process in [x
                          for x in psutil.process_iter()
                          if len(x.cmdline()) > 0 and os.path.basename(x.exe()) == BINNAME]:
        try:
            redis_ip, redis_port = sorted([laddr.laddr
                                           for laddr in redis_process.get_connections()
                                           if laddr.status == 'LISTEN'])[0]
        except:
            continue
        redis_passwd = ''
        config_files = []
        if os.path.isdir(redis_process.getcwd()):
            config_files.append(os.path.join(redis_process.getcwd() , redis_conf_file_name))
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
def get_redis_data(instance_name, *args):
    """
    get monitor data from redis
    @param instance_name: ip:port:passwd
    @return: dict
    """

    ip, port, passwd = instance_name.split('/')
    r = redis.StrictRedis(host=ip, port=port, password=passwd)
    d = r.info()
    check_items = {
        'redis_version': str,
        'redis_mode': str,  # standalone,
        'uptime_in_seconds': int,
        'process_id':int,
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
    redis_stats['role']=1 if redis_stats.get('role','master') == 'master' else 2
    redis_stats['keyspace_hits_rate']='{0:.2f}'.format(float(redis_stats.get('keyspace_hits',0))/float(redis_stats.get('keyspace_hits',1)+redis_stats.get('keyspace_misses',0))*100)
    if redis_stats['connected_slaves'] > 0:
        slave_lists = set()
        for i in range(redis_stats['connected_slaves']):
            if d.has_key("slave%s" % i):
                slave_lists.add(str(d["slave%s" % i]))
        redis_stats['slave_lists'] = ','.join(list(slave_lists))
    return redis_stats
