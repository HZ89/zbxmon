#!/opt/17173_install/python-2.7.6/bin/python2.7
"""
This script creates Zabbix template and agent config from the existing
Perl definitions for Cacti and triggers if defined.

License: GPL License (see COPYING)
Copyright: 2013 Percona
Authors: Roman Vynar
"""
from extool import dict2xml

"""
change: 修改自percona monitor plugin文件包，增加 -d / --define 参数，接受cacti define 文件，讲结果导出成zabbix模板
如:percona/cacti/definitions/mysql.def
author：Jianpo Ma  majianpo@cyou-inc.com
"""
import getopt
import re
import sys
import time
import yaml
import string
import os
import StringIO

VERSION = float("%d.%d" % (sys.version_info[0], sys.version_info[1]))
if VERSION < 2.6:
    sys.stderr.write("ERROR: python 2.6+ required. Your version %s is too ancient.\n" % VERSION)
    sys.exit(1)

# 17173 zabbix version
ZABBIX17173='2.2.0'
use_discovery_rules=True
has_extend=True


# Constants
ZABBIX_VERSION = '2.0'
ZABBIX_SCRIPT_PATH = '/opt/17173_install/zabbix-%s/externalscripts/service_monitor.py' % ZABBIX17173

item_types = {'Zabbix agent': 0,
              'Zabbix agent (active)': 7,
              'Simple check': 3,
              'SNMPv1': 1,
              'SNMPv2': 4,
              'SNMPv3': 6,
              'SNMP Trap': 17,
              'Zabbix Internal': 5,
              'Zabbix Trapper': 2,
              'Zabbix Aggregate': 8,
              'External check ': 10,
              'Database monitor': 11,
              'IPMI agent': 12,
              'SSH agent': 13,
              'TELNET agent': 14,
              'JMX agent': 16,
              'Calculated': 15}

item_value_types = {'Numeric (unsigned)': 3,
                    'Numeric (float)': 0,
                    'Character': 1,
                    'Log': 2,
                    'Text': 4}

# Cacti to Zabbix relation
item_store_values = {1: 0,  # GAUGE == As is
                     2: 1,  # COUNTER == Delta (speed per second)
                     3: 1}  # DERIVE == Delta (speed per second)
# Others: Delta (simple change) 2

graph_types = {'Normal': 0,
               'Stacked': 1,
               'Pie': 2,
               'Exploded': 3}

graph_item_functions = {'all': 7,
                        'min': 1,
                        'avg': 2,
                        'max': 4}

# Cacti to Zabbix relation
graph_item_draw_styles = {'LINE1': 0,  # Line
                          'LINE2': 2,  # Bold line
                          'AREA':  1,  # Filled region
                          'STACK': 0}  # Line
# Others: Dot 3, Dashed line 4, Gradient line 5

graph_y_axis_sides = {'Left': 0,
                      'Right': 1}

trigger_severities = {'Not_classified ': 0,
                      'Information': 1,
                      'Warning': 2,
                      'Average': 3,
                      'High': 4,
                      'Disaster': 5}

# Parse args
usage = """
    -h, --help                    Prints this menu and exits
    -o, --output [xml|config]     Type of the output, default - xml.
    -d, --definition              cacti def file
    -t, --trigger                 trigger yaml file
    -u, --user                    need to create USER macro
    -p, --password                need to create PASSWD macro
"""
# DEFINITION = 'percona/cacti/definitions/mysql.def'
# PHP_SCRIPT = 'percona/cacti/scripts/ss_get_mysql_stats.php'
# TRIGGERS = 'percona/zabbix/triggers/mysql.yml'
DEFINITION=None
PHP_SCRIPT=None
TRIGGERS=None
need_auth=False
auth_str=[]
try:
    opts, args = getopt.getopt(sys.argv[1:], "ho:vd:t:up", ["help", "output="])
except getopt.GetoptError as err:
    sys.stderr.write('%s\n%s' % (err, usage))
    sys.exit(2)
# Defaults
output = 'xml'
verbose = False
if len(opts)==0:
    print "must suppose paramaters"
    print usage
    sys.exit()
for o, a in opts:
    if o == "-v":
        verbose = True
    elif o in ("-h", "--help"):
        print usage
        sys.exit()
    elif o in ("-o", "--output"):
        output = a
        if output not in ['xml', 'config']:
            sys.stderr.write('invalid output type\n%s' % usage)
            sys.exit(2)
    elif o in ("-d","--definition"):
        assert a is not None, "must suppose the cacti definition file. example:percona/cacti/definitions/mysql.def"
        assert os.path.exists(a),"cacti file not exists:%s" % a
        DEFINITION=a
    elif o in ("-t","--trigger"):
        assert os.path.exists(a),"trigger file not exists:%s" % a
        TRIGGERS=a
    elif o in ("-u", "--user"):
        need_auth=True
        auth_str.append("{$USER}")
    elif o in ("-p", "--password"):
        need_auth=True
        auth_str.append("{$PASSWD}")
    else:
        assert False, "unhandled option"
if need_auth:
    auth_str='/'.join(auth_str)
# Read Cacti template definition file and load as YAML
dfile = open(DEFINITION, 'r')
data = []
for line in dfile.readlines():
    if not line.strip().startswith('#'):
        data.append(line.replace('=>', ':'))
data = yaml.safe_load(' '.join(data))

# for key in data.keys():
#     if key in ['hash','inputs','checksum']: data.pop(key)
#     for graph in data['graphs']:
#         if graph.has_key('hash'):graph.pop('hash')
#         for item in graph['items']:
#             if item.has_key('hashes'):item.pop('hashes')
#             if item.has_key('task'):item.pop('task')
#             if not item.has_key('data_source_type_id'):item['data_source_type_id']=graph['dt'][item['item']]['data_source_type_id']
#         if graph.has_key('dt'):graph.pop('dt')
#
# with open('mysql_tmpl','wr') as mf:
#     mf.writelines(json.dumps(data,indent=4,sort_keys=True))
#     mf.flush()


# Define the base of Zabbix template
tmpl = dict()
app_name = data['name'].split()[0]
if str(app_name).lower() == 'memcached':
    app_name="Memcache"
tmpl_name = '17173 %s Template' % data['name']
tmpl['version'] = ZABBIX_VERSION
tmpl['date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
tmpl['groups'] = {'group': {'name': 'Percona Templates'}}
tmpl['screens'] = {'screen': {'name': '%s Graphs' % app_name,
                              'hsize': 2,
                              'vsize': int(round(len(data['graphs']) / 2.0)),
                              'screen_items': {'screen_item': []}}}
tmpl['templates'] = {'template': {'template': tmpl_name,
                                  'name': tmpl_name,
                                  'groups': tmpl['groups'],
                                  'applications': {'application': {'name': app_name }},
                                  }}
if not use_discovery_rules:
    tmpl['graphs'] = {'graph': []}
    tmpl['triggers'] = ''
    tmpl['templates']['template']['items']={'item': []}
    tmpl['templates']['template']['macros']=''

# discovery rules
if use_discovery_rules:
    tmpl['templates']['template']['discovery_rules']={'discovery_rule': {
        'name':"%s discovery" % str(app_name).lower(),
        'type':item_types['Zabbix agent (active)'],
        'key':"service.discovery[%s,HOST/PORT%s]" % (str(app_name).lower(),'' if not need_auth else ','+ auth_str),
        'delay':3600,
        'status':0,
        'lifetime':3,
        'item_prototypes':{'item_prototype':[]},

        'graph_prototypes':{'graph_prototype':[]}
    }}
if need_auth:
    tmpl['templates']['template']['macros']={
        'macro':[
            {'macro':'{$USER}','value':'zabbixmonitor'},
            {'macro':'{$PASSWD}','value':'zabbixmonitor'}
        ]
    }


def format_item(f_item):
    """Underscore makes an agent to throw away the support for item
    """
    for prefix in ("MONGODB_","MEMC_","REDIS_"):
        f_item=str(f_item).replace(prefix,"") if str(f_item).startswith(prefix) else f_item
    return '%s.%s' % (app_name, f_item.replace('_', '-'))
def format_key(f_item):
    macro='{#HOST}/{#PORT}/{#PASSWD}' if str(app_name).lower().strip()=='redis' else '{#HOST}/{#PORT}'
    key=str(f_item).replace(' ','_').lower().strip()
    if key.find(str(app_name).lower().strip()) == 0:
        key=key.replace(str(app_name).lower().strip()+'_','',1)
    if key.find('memc_')==0:
        key=key.replace('memc_','',1)
    param=[str(app_name).lower().strip(),
          key,
          None if not use_discovery_rules else macro,
          None if not need_auth else auth_str ]
    return  "service.status[%s]" % ','.join([i for i in param if i is not None])
def format_name(f_item):
    f_item = f_item.replace('_', ' ').replace('-',' ').title()
    f_item = re.sub(r'^[A-Z]{4,} ', '', f_item)
    if f_item.startswith('Memc'):
        f_item=f_item.replace("Memc",'').strip()
    if f_item.startswith(app_name.title()):
        f_item=f_item.replace(app_name.title(),'',1)
    f_item.strip()

    param=[None if not use_discovery_rules else '{#HOST}:{#PORT}',
           str(app_name).title(),
           str(f_item).replace('_',' ').replace('-',' ').strip().title()]
    return ' '.join([i for i in param if i is not None])

# Parse definition
all_item_keys = set()
x = y = 0
for graph in data['graphs']:
    # Populate graph
    z_graph = {'name': format_name(graph['name']),
               'width': 900,
               'height': 200,
               'graphtype': graph_types['Normal'],
               'show_legend': 1,
               'show_work_period': 1,
               'show_triggers': 1,
               'ymin_type': 0,  # Calculated
               'ymax_type': 0,  # Calculated
               'ymin_item_1': 0,
               'ymax_item_1': 0,
               'show_3d': 0,
               'percent_left': '0.00',
               'percent_right': '0.00',
               'graph_items': {'graph_item': []}}

    # Populate graph items
    multipliers = dict()
    i = 0
    for item in graph['items']:
        if item not in ['hash', 'task']:
            draw_type = item['type']
            if draw_type not in graph_item_draw_styles.keys():
                sys.stderr.write("ERROR: Cacti graph item type %s is not supported for item %s.\n" % (draw_type, item['item']))
                sys.exit(1)
            cdef = item.get('cdef')
            if cdef == 'Negate':
                multipliers[item['item']] = (1, -1)
            elif cdef == 'Turn Into Bits':
                multipliers[item['item']] = (1, 8)
            elif cdef:
                sys.stderr.write("ERROR: CDEF %s is not supported for item %s.\n" % (cdef, item['item']))
                sys.exit(1)
            else:
                multipliers[item['item']] = (0, 1)
            z_graph_item = {'item': {'key': format_key(item['item']),
                                     'host': tmpl_name},
                            'calc_fnc': graph_item_functions['avg'],
                            'drawtype': graph_item_draw_styles[draw_type],
                            'yaxisside': graph_y_axis_sides['Left'],
                            'color': item['color'],
                            'sortorder': i,
                            'type': 0}
            z_graph['graph_items']['graph_item'].append(z_graph_item)

            i = i + 1
    if not use_discovery_rules:
        tmpl['graphs']['graph'].append(z_graph)
    else:
        tmpl['templates']['template']['discovery_rules']['discovery_rule']['graph_prototypes']['graph_prototype'].append(z_graph)

    # Add graph to the screen
    if not use_discovery_rules:
        z_screen_item = {'resourcetype': 0,  # Graph
                         'width': 500,
                         'height': 120,
                         'valign': 1,  # Middle
                         'halign': 0,  # Center
                         'colspan': 1,
                         'rowspan': 1,
                         'x': x,
                         'y': y,
                         'dynamic': 1,
                         'resource': {'name': graph['name'],
                                      'host': tmpl_name}}
        tmpl['screens']['screen']['screen_items']['screen_item'].append(z_screen_item)
        tmpl['templates']['template']['screens'] = tmpl['screens']

    #
    if x == 0:
        x = 1
    else:
        x = 0
        y = y + 1


    # Populate items
    for item in graph['dt'].keys():
        if item not in ['hash', 'input']:
            ds_type = int(graph['dt'][item]['data_source_type_id'])
            if ds_type == 4:
                sys.stderr.write("ERROR: Cacti DS type ABSOLUTE is not supported for item %s.\n" % item)
                sys.exit(1)

            # name = item.replace('_', ' ').title()
            # name = re.sub(r'^[A-Z]{4,} ', '', name)
            # if name.startswith('Memc'):
            #     name=name.replace("Memc",'').strip()
            # if not name.startswith(app_name.title()):
            #     name=' '.join([app_name.title(),name])
            n_item=str(item).lower()
            if n_item.startswith(app_name.lower()):
                n_item=n_item.replace(app_name.lower()+'_','',1)
            if n_item  in all_item_keys:continue
            if str(n_item).startswith('memc_'):
                n_item=str(n_item).replace('memc_','',1)
            base_value = int(graph['base_value'])
            if base_value == 1000:
                unit = ''
            elif base_value == 1024:
                unit = 'B'
            else:
                sys.stderr.write("ERROR: base_value %s is not supported for item %s.\n" % (base_value, item))
                sys.exit(1)

            z_item = {'name': format_name(n_item),
                      'type': item_types['Zabbix agent (active)'],
                      'key': format_key(n_item),
                      'value_type': item_value_types['Numeric (unsigned)'],
                      'data_type': 0,  # Decimal the above is Numeric (unsigned)
                      'units': unit,
                      'delay': 30,  # Update interval (in sec)
                      'history': 90,
                      'trends': 365,
                      'delta': item_store_values[ds_type],
                      'applications': {'application': {'name': app_name }},
                      'description': format_name(n_item),
                      'multiplier': multipliers[item][0],
                      'formula': multipliers[item][1],
                      'status': 0}
            if not use_discovery_rules:
                tmpl['templates']['template']['items']['item'].append(z_item)
            else:
                tmpl['templates']['template']['discovery_rules']['discovery_rule']['item_prototypes']['item_prototype'].append(z_item)
            all_item_keys.add(n_item)

# Generate output
if output == 'xml':
    # Add extra items required by triggers
    if has_extend:
        extra_memcache = '''
accepting_conns
auth_cmds
auth_errors
bytes
bytes_read
bytes_written
cas_badval
cas_hits
cas_misses
cmd_flush
cmd_get
cmd_set
cmd_touch
conn_yields
connection_structures
curr_connections
curr_items
decr_hits
decr_misses
delete_hits
delete_misses
evicted_unfetched
evictions
expired_unfetched
get_hits
get_hits_ratio
get_misses
hash_bytes
hash_is_expanding
hash_power_level
incr_hits
incr_misses
libevent
limit_maxbytes
listen_disabled_num
pid
pointer_size
reclaimed
reserved_fds
rusage_system
rusage_user
threads
time
total_connections
total_items
touch_hits
touch_misses
uptime
version
        '''
        extra_mongo='''
connections_available
connections_current
connections_totalCreated
dur_commits
dur_journaledMB
dur_timeMs_writerToDataFiles
dur_timeMs_writerToJournal
dur_writeToDataFilesMB
globalLock_activeClients_readers
globalLock_activeClients_total
globalLock_activeClients_writes
host
indexCounters_hits
indexCounters_missRatio
indexCounters_misses
mem_resident
mem_virtual
network_bytesIn
network_bytesOut
network_numRequests
opcounters_delete
opcounters_getmore
opcounters_insert
opcounters_query
opcounters_update
uptime
version
        '''
        extra_redis='''
aof_current_rewrite_time_sec
aof_enabled
aof_last_bgrewrite_status
aof_last_rewrite_time_sec
aof_rewrite_in_progress
aof_rewrite_scheduled
arch_bits
blocked_clients
client_biggest_input_buf
client_longest_output_list
connected_clients
connected_slaves
evicted_keys
expired_keys
gcc_version
hz
instantaneous_ops_per_sec
keyspace_hits
keyspace_misses
latest_fork_usec
loading
lru_clock
mem_allocator
mem_fragmentation_ratio
multiplexing_api
os
process_id
pubsub_channels
pubsub_patterns
rdb_bgsave_in_progress
rdb_changes_since_last_save
rdb_current_bgsave_time_sec
rdb_last_bgsave_status
rdb_last_bgsave_time_sec
rdb_last_save_time
redis_git_dirty
redis_git_sha1
redis_mode
redis_version
rejected_connections
role
run_id
tcp_port
total_commands_processed
total_connections_received
uptime_in_days
uptime_in_seconds
used_cpu_sys
used_cpu_sys_children
used_cpu_user
used_cpu_user_children
used_memory
used_memory_human
used_memory_lua
used_memory_peak
used_memory_peak_human
used_memory_rss
        '''
        extra_mysql='''
slave_running
        '''
        extra=''
        if app_name.lower() == 'redis':
            extra=extra_redis
        elif app_name.lower() == 'mongodb':
            extra=extra_mongo
        elif app_name.lower() == 'memcache':
            extra=extra_memcache
        elif app_name.lower() == 'mysql':
            extra=extra_mysql
        eif=StringIO.StringIO(extra)
        for eitem in eif.readlines():
            eitem=str(eitem).strip()
            if len(eitem)==0: continue
            if eitem in all_item_keys: continue

            z_item = {'name': format_name(eitem),
                      'key': format_key(eitem),
                      'type': item_types['Zabbix agent (active)'],
                      'value_type': item_value_types['Numeric (unsigned)'],
                      'data_type': 0,
                      'delay': 30,  # Update interval (in sec)
                      'history': 90,
                      'trends': 365,
                      'delta': 0,  # As is
                      'applications': {'application': {'name': app_name }},
                      'description': eitem,
                      'status': 0}
            if not use_discovery_rules:
                tmpl['templates']['template']['items']['item'].append(z_item)
            else:
                tmpl['templates']['template']['discovery_rules']['discovery_rule']['item_prototypes']['item_prototype'].append(z_item)
            all_item_keys.add(eitem)

    # Read triggers from YAML file
    if TRIGGERS and len(TRIGGERS)>0 and os.path.exists(TRIGGERS):
        dfile = open(TRIGGERS, 'r')
        data = yaml.safe_load(dfile)

        # Populate triggers
        trigger_refs = dict((t['name'], t['expression'].replace('TEMPLATE', tmpl_name)) for t in data)
        if use_discovery_rules:
            tmpl['templates']['template']['discovery_rules']['discovery_rule']['trigger_prototypes']={'trigger_prototype':[]}
        else:
            tmpl['triggers'] = {'trigger': []}
        for trigger in data:
            if trigger['name'] == 'MySQL is down on {HOST.NAME}':continue
            z_trigger = {'name': trigger['name'] if not use_discovery_rules else "{#HOST}:{#PORT} %s" % trigger['name'],
                         #{17173 MySQL Server Template:MySQL.Aborted-clients[{#HOST}:{#PORT},{$USER},{$PASSWD}].last()}=0
                         'expression': string.Template( trigger['expression'].replace('TEMPLATE', tmpl_name)).safe_substitute(macro='' if not use_discovery_rules else '[{#HOST}:{#PORT},{$USER},{$PASSWD}]'),
                         'priority': trigger_severities[trigger.get('severity', 'Not_classified')],
                         'status': 0,  # Enabled
                        }
            # Populate trigger dependencies
            if not use_discovery_rules:
                z_trigger['dependencies']=''
                if trigger.get('dependencies'):
                    z_trigger['dependencies'] = {'dependency': []}
                    for dep in trigger['dependencies']:
                        exp = trigger_refs.get(dep)
                        if not exp:
                            sys.stderr.write("ERROR: Dependency trigger '%s' is not defined for trigger '%s'.\n" % (dep, trigger['name']))
                            sys.exit(1)
                        z_trigger_dep = {'name': dep,
                                         'expression': exp}
                        z_trigger['dependencies']['dependency'].append(z_trigger_dep)
            if not use_discovery_rules:
                tmpl['triggers']['trigger'].append(z_trigger)
            else:
                tmpl['templates']['template']['discovery_rules']['discovery_rule']['trigger_prototypes']['trigger_prototype'].append(z_trigger)

    # Convert and write XML
    xml = dict2xml.Converter(wrap='zabbix_export', indent='  ').build(tmpl)
    print '<?xml version="1.0" encoding="UTF-8"?>\n%s' % xml

elif output == 'config':
    # Read Perl hash aka MAGIC_VARS_DEFINITIONS from Cacti PHP script
    data = []
    if PHP_SCRIPT and len(PHP_SCRIPT)>0 and os.path.exists(PHP_SCRIPT):
        dfile = open(PHP_SCRIPT, 'r')
        store = 0
        for line in dfile.readlines():
            line = line.strip()
            if not line.startswith('#'):
                if store == 1:
                    if line == ');':
                        break
                    data.append(line.replace('=>', ':'))
                elif line == '$keys = array(':
                    store = 1
        data = yaml.safe_load('{%s}' % ' '.join(data))
    else:
        data={}

    # Write Zabbix agent config
    service_name=str(app_name).lower()
    print "UserParameter=service.discovery[*],%s  --service=$1 --discovery --macros=$2,$3 --extend=$4,$5" % ZABBIX_SCRIPT_PATH

    print "UserParameter=service.status[*],%s --service=$1 --item=$2 --instance=$3 --extend=$4,$5 " % ZABBIX_SCRIPT_PATH

    # Write extra items
    #print "UserParameter=%s[*],%s/service_monitor.py --service=mysql --instance=$1,$2 --extend=$3,$4 --item=running-slave" % (format_item('running-slave'), ZABBIX_SCRIPT_PATH)
