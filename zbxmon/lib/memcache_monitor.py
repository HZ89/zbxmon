# -*- coding: utf8 -*-

import memcache

BINNAME = 'memcached'

def get_memcache_data(instance_name):
    """
    the func used to get memcache data
    @param instance_name: the ip:port of memcached instance
    @return: dict
    """

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
        result[ckey] = check_keys[ckey](status[ckey] if status.has_key(ckey) else '0')
    hits_ratio_cmds = ['get', 'delete', 'incr', 'decr', 'cas', 'touch']
    for cmd in hits_ratio_cmds:
        hit_key = "%s_hits" % cmd
        miss_key = "%s_misses" % cmd
        result["%s_hists_ratio" % cmd]='{0:.2f}'.format(
                        float(result.get(hit_key,0))/float(result.get(hit_key,1)+result.get(miss_key,0))*100.00
        )
    return result
