# -*- coding: utf8 -*-


import pymongo


def get_mongodb_data(instance_name, mongo_user, mongo_passwd):
    """
    the func used to get mongodb data
    @param instance_name: the ip:port of mongodb
    @return: dict
    """

    instance_name = str(instance_name).replace('/', ':')
    uri = "mongodb://{}:{}@{}/admin".format(mongo_user, mongo_passwd, instance_name)
    db = pymongo.MongoClient(uri)
    coll = db.admin
    status = None
    rs_status = None
    try:
        status=coll.command('serverStatus', 1)
    except:
        pass
    try:
        rs_status=coll.command('replSetGetStatus',1)
    except:
        pass
    db.disconnect()
    mongo_status = {}
    if status:
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
    mongo_status['replset_delay']=0
    if rs_status:
        rs_members=[i['optime'] for i in rs_status['members'] if i['name']==instance_name or i['stateStr']=='PRIMARY']
        if len(rs_members) == 2:
            mongo_status['replset_delay']=abs(rs_members[0]-rs_members[1])

    for key in mongo_status.keys():
        mongo_status[key.lower()] = mongo_status.pop(key)
    return mongo_status