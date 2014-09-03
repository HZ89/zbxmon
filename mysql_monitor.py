#!/opt/17173_install/python-2.7.6/bin/python2.7
#coding:utf-8
__author__ = 'Justin Ma'
import os,sys
import string
import re
import MySQLdb
import traceback
from MySQLdb.cursors import Cursor,DictCursor
class MySQL_Monitor(object):
    sections_struct=[
        #{'title':'BACKGROUND THREAD',
         #'reg':None
         #},
        {'title':'SEMAPHORES',
         'bound':r"[FILE I/O|TRANSACTIONS]",
         },
        {'title':'FILE I/O',
         'bound':'INSERT BUFFER AND ADAPTIVE HASH INDEX',
         },
        {'title':'INSERT BUFFER AND ADAPTIVE HASH INDEX',
         'bound':'LOG',
         },
        {'title':'LOG',
         'bound':'BUFFER POOL AND MEMORY',
         },
        {'title':'BUFFER POOL AND MEMORY',
         'bound':'[INDIVIDUAL BUFFER POOL INFO|ROW OPERATIONS]',
         },
        {'title':'INDIVIDUAL BUFFER POOL INFO', #mysql 5.6
         'bound':'ROW OPERATIONS',
         },
        {'title':'ROW OPERATIONS',
         'bound':'[TRANSACTIONS|END OF INNODB MONITOR OUTPUT]'
         },
        {'title':'TRANSACTIONS',
         'bound':'[END OF INNODB MONITOR OUTPUT|FILE I/O]'
         }
    ]    

    @classmethod
    def discovery(cls):
        pass
    @classmethod
    def get_innodb_status(cls, text):
        status={
            'spin_waits'                : [],
            'spin_rounds'               : [],
            'os_waits'                  : [],
            'pending_normal_aio_reads'  : 0, 
            'pending_normal_aio_writes' : 0, 
            'pending_ibuf_aio_reads'    : 0, 
            'pending_aio_log_ios'       : 0, 
            'pending_aio_sync_ios'      : 0, 
            'pending_log_flushes'       : 0, 
            'pending_buf_pool_flushes'  : 0, 
            'file_reads'                : 0, 
            'file_writes'               : 0, 
            'file_fsyncs'               : 0, 
            'ibuf_inserts'              : 0, 
            'ibuf_merged'               : 0, 
            'ibuf_merges'               : 0, 
            'log_bytes_written'         : 0, 
            'unflushed_log'             : 0, 
            'log_bytes_flushed'         : 0, 
            'pending_log_writes'        : 0, 
            'pending_chkp_writes'       : 0, 
            'log_writes'                : 0, 
            'pool_size'                 : 0, 
            'free_pages'                : 0, 
            'database_pages'            : 0, 
            'modified_pages'            : 0, 
            'pages_read'                : 0, 
            'pages_created'             : 0, 
            'pages_written'             : 0, 
            'queries_inside'            : 0, 
            'queries_queued'            : 0, 
            'read_views'                : 0, 
            'rows_inserted'             : 0, 
            'rows_updated'              : 0, 
            'rows_deleted'              : 0, 
            'rows_read'                 : 0, 
            'innodb_transactions'       : 0, 
            'unpurged_txns'             : 0, 
            'history_list'              : 0, 
            'current_transactions'      : 0, 
            'active_transactions'       : 0, 
            'hash_index_cells_total'    : 0, 
            'hash_index_cells_used'     : 0, 
            'total_mem_alloc'           : 0, 
            'additional_pool_alloc'     : 0, 
            'last_checkpoint'           : 0, 
            'uncheckpointed_bytes'      : 0, 
            'ibuf_used_cells'           : 0, 
            'ibuf_free_cells'           : 0, 
            'ibuf_cell_count'           : 0, 
            'adaptive_hash_memory'      : 0, 
            'page_hash_memory'          : 0, 
            'dictionary_cache_memory'   : 0, 
            'file_system_memory'        : 0, 
            'lock_system_memory'        : 0, 
            'recovery_system_memory'    : 0, 
            'thread_hash_memory'        : 0, 
            'innodb_sem_waits'          : 0, 
            'innodb_sem_wait_time_ms'   : 0, 
            'innodb_lock_wait_secs'     : 0, 
            'innodb_tables_in_use'      : 0, 
            'innodb_locked_tables'      : 0, 
            'innodb_lock_structs'       : 0, 
            'locked_transactions'       : 0, 
            'innodb_io_pattern_memory'  : 0,             
        }
        txn_seen = False
        line=''
        prev_line=''
        for line in string.split(text,'\n'):
            line=string.strip(line)
            if line == '': continue
            row=None
            try:
                #SEMAPHORES
                if line.startswith('Mutex spin waits'):
                    # Mutex spin waits 79626940, rounds 157459864, OS waits 698719
                    row=[int(i) for i in re.findall('Mutex spin waits (\d+), rounds (\d+), OS waits (\d+)',line)[0] if len(i)>0]
                    status['spin_waits'].append(row[0])
                    status['spin_rounds'].append(row[1])
                    status['os_waits'].append(row[2])
                elif line.startswith('RW-shared spins'):
                    # RW-shared spins 3859028, OS waits 2100750; RW-excl spins 4641946, OS waits 1530310
                    # Post 5.5.17 SHOW ENGINE INNODB STATUS syntax
                    # RW-shared spins 604733, rounds 8107431, OS waits 241268
                    row=[int(i) for i in re.findall('RW-shared spins (\d+),(?: rounds (\d+),)? OS waits (\d+)',line)[0] if len(i)>0]
                    if len(row)==3:  row.pop(1)
                    status['spin_waits'].append(row[0])
                    status['os_waits'].append(row[1])
                elif line.find('RW-excl spins') != -1:
                    # RW-shared spins 3859028, OS waits 2100750; RW-excl spins 4641946, OS waits 1530310
                    # Post 5.5.17 SHOW ENGINE INNODB STATUS syntax
                    # RW-excl spins 604733, rounds 8107431, OS waits 241268
                    row=[int(i) for i in re.findall('RW-excl spins (\d+),(?: rounds (\d+),)? OS waits (\d+)',line)[0] if len(i)>0]
                    if len(row)==3:  row.pop(1)
                    status['spin_waits'].append(row[0])
                    status['os_waits'].append(row[1])
                elif line.find('seconds the semaphore:') != -1:
                    # --Thread 907205 has waited at handler/ha_innodb.cc line 7156 for 1.00 seconds the semaphore:
                    status['innodb_sem_waits']+=1
                    row=re.findall('for (\d+.\d+) seconds the semaphore:',line)[0]
                    status['innodb_sem_wait_time_ms']+=float(row[0])*1000
                #TRANSACTIONS
                elif line.startswith('Trx id counter'):
                    # The beginning of the TRANSACTIONS section: start counting
                    # transactions
                    # Trx id counter 0 1170664159
                    # Trx id counter 861B144C
                    row=[i for i in re.findall('Trx id counter(?: (\d+))? (\w+)',line)[0] if len(i)>0]
                    status['innodb_transactions']=int(row[0] if len(row) == 1 else row[0]+row[1],16)
                    txn_seen=True
                elif line.startswith('Purge done for trx'):
                    # Purge done for trx's n:o < 0 1170663853 undo n:o < 0 0
                    # Purge done for trx's n:o < 861B135D undo n:o < 0
                    row=[i for i in re.findall('''Purge done for trx's n:o <(?: (\w+))? (\w+) undo n:o < 0 0''',line)[0] if len(i)>0]
                    status['unpurged_txns']=status['innodb_transactions']-int(row[0] if len(row) == 1 else row[0]+row[1],16)
                elif line.startswith('History list length'):
                    #History list length 1557
                    row=re.findall('History list length (\d+)',line)
                    status['history_list']=int(row[0])
                elif txn_seen and line.startswith('---TRANSACTION'):
                    # ---TRANSACTION 0, not started, process no 13510, OS thread id 1170446656
                    #---TRANSACTION 6D8BB4768, not started
                    status['current_transactions']+=1
                    if line.find('ACTIVE') != -1: status['active_transactions']+=1
                elif txn_seen and line.startswith('------- TRX HAS BEEN'):
                    # ------- TRX HAS BEEN WAITING 32 SEC FOR THIS LOCK TO BE GRANTED:
                    row=re.findall('TRX HAS BEEN WAITING (\d+) SEC FOR THIS LOCK TO BE GRANTED',line)
                    status['innodb_lock_wait_secs']+=int(row[0])
                elif line.find('read views open inside InnoDB') != -1:
                    # 1 read views open inside InnoDB
                    row=re.findall('(\d+) read views open inside InnoDB',line)
                    status['read_views']+=int(row[0])
                elif line.startswith('mysql tables in use'):
                    # mysql tables in use 2, locked 2
                    row=re.findall('mysql tables in use (\d+), locked (\d+)',line)[0]
                    status['innodb_tables_in_use']+=int(row[0])
                    status['innodb_locked_tables']+=int(row[1])
                elif txn_seen and line.find('lock struct(s)') != -1:
                    # 23 lock struct(s), heap size 3024, undo log entries 27
                    # LOCK WAIT 12 lock struct(s), heap size 3024, undo log entries 5
                    row=re.findall('(\d+) lock struct(s)',line)[0]
                    status['innodb_lock_structs']+=int(row[0])
                    if line.startswith('LOCK WAIT'):
                        status['locked_transactions']+=row[0]
                # FILE I/O
                elif line.find(' OS file reads, ') != -1:
                    # 8782182 OS file reads, 15635445 OS file writes, 947800 OS fsyncs
                    row=re.findall('(\d+) OS file reads, (\d+) OS file writes, (\d+) OS fsyncs',line)[0]
                    status['file_reads']=int(row[0])
                    status['file_writes']=int(row[1])
                    status['file_fsyncs']=int(row[2])
                elif line.startswith('Pending normal aio reads:'):
                    # Pending normal aio reads: 0, aio writes: 0,
                    row=re.findall('Pending normal aio reads: (\d+).*, aio writes: (\d+).*,',line)[0]
                    status['pending_normal_aio_reads']=int(row[0])
                    status['pending_normal_aio_writes']=int(row[1])
                elif line.startswith('ibuf aio reads'):
                    #  ibuf aio reads: 0, log i/o's: 0, sync i/o's: 0
                    row=re.findall('''ibuf aio reads: (\d+), log i/o's: (\d+), sync i/o's: (\d+)''',line)[0]
                    status['pending_ibuf_aio_reads']=int(row[0])
                    status['pending_aio_log_ios']=int(row[1])
                    status['pending_aio_sync_ios']=int(row[2])
                elif line.startswith('Pending flushes (fsync)'):
                    # Pending flushes (fsync) log: 0; buffer pool: 0
                    row=re.findall('Pending flushes (fsync) log: (\d+); buffer pool: (\d+)')[0]
                    status['pending_log_flushes']=int(row[0])
                    status['pending_buf_pool_flushes']=int(row[1])
                # INSERT BUFFER AND ADAPTIVE HASH INDEX
                elif line.startswith('Ibuf for space 0: size '):
                    # Older InnoDB code seemed to be ready for an ibuf per tablespace.  It
                    # had two lines in the output.  Newer has just one line, see below.
                    # Ibuf for space 0: size 1, free list len 887, seg size 889, is not empty
                    # Ibuf for space 0: size 1, free list len 887, seg size 889,
                    row=re.findall('Ibuf for space 0: size (\d+), free list len (\d+), seg size (\d+)',line)[0]
                    status['ibuf_used_cells']=int(row[0])
                    status['ibuf_free_cells']=int(row[1])
                    status['ibuf_cell_count']=int(row[2])
                elif line.startswith('Ibuf: size '):
                    # Ibuf: size 1, free list len 4634, seg size 4636,
                    #Ibuf: size 1, free list len 11, seg size 13, 17 merges
                    row=[i for i in re.findall('Ibuf: size (\d+), free list len (\d+), seg size (\d+),(?: (\d+) merges)?',line)[0] if len(i)>0]
                    status['ibuf_used_cells']=int(row[0])
                    status['ibuf_free_cells']=int(row[1])
                    status['ibuf_cell_count']=int(row[2])
                    if len(row)==4:
                        status['ibuf_merged']=int(row[3])
                elif line.find(', delete mark ') != -1 and prev_line.startswith('merged operations:'):
                    # Output of show engine innodb status has changed in 5.5
                    # merged operations:
                    # insert 593983, delete mark 387006, delete 73092
                    row=re.findall(' insert (\d+), delete mark (\d+), delete (\d+)',line)[0]
                    status['ibuf_inserts']=int(row[0])
                    status['ibuf_merged']=int(row[0])+int(row[1])+int(row[2])
                elif line.find(' merged recs, ') != -1:
                    # 19817685 inserts, 19817684 merged recs, 3552620 merges
                    row=[int(i) for i in re.findall('(d+) inserts, (\d+) merged recs, (\d+) merges',line)[0]]
                    status['ibuf_inserts']=row[0]
                    status['ibuf_merged']=row[1]
                    status['ibuf_merges']=row[2]
                elif line.startswith('Hash table size '):
                    # In some versions of InnoDB, the used cells is omitted.
                    # Hash table size 4425293, used cells 4229064, ....
                    # Hash table size 57374437, node heap has 72964 buffer(s) <-- no used cells
                    row=[int(i) for i in re.findall('Hash table size (\d+),(?: used cells (\d+))?',line)[0] if len(i)>0]
                    status['hash_index_cells_total']=row[0]
                    if len(row)==2:
                        status['hash_index_cells_used']=row[1]
                # LOG
                elif line.find(''' log i/o's done, ''') != -1:
                    # 3430041 log i/o's done, 17.44 log i/o's/second
                    # 520835887 log i/o's done, 17.28 log i/o's/second, 518724686 syncs, 2980893 checkpoints
                    # TODO: graph syncs and checkpoints
                    row=re.findall("(\d+) log i/o's done",line)
                    status['log_writes']=int(row[0])
                elif line.find(' pending log writes, ') !=-1:
                    # 0 pending log writes, 0 pending chkp writes
                    row=[int(i) for i in re.findall('(\d+) pending log writes, (\d+) pending chkp writes',line)[0]]
                    status['pending_log_writes']=row[0]
                    status['pending_chkp_writes']=row[1]
                elif line.startswith('Log sequence number'):
                    # This number is NOT printed in hex in InnoDB plugin.
                    # Log sequence number 13093949495856 //plugin
                    # Log sequence number 125 3934414864 //normal
                    row=[i for i in re.findall('Log sequence number (\w+)(?: (\w+))?',line)[0] if len(i)>0]
                    status['log_bytes_written']=int(row[0]) if len(row)==1 else int(row[0]+row[1],16)
                elif line.startswith('Log flushed up to'):
                    # This number is NOT printed in hex in InnoDB plugin.
                    # Log flushed up to   13093948219327
                    # Log flushed up to   125 3934414864
                    row=[i for i in re.findall('Log flushed up to   (\w+)(?: (\w+))?',line)[0] if len(i)>0]
                    status['log_bytes_flushed']=int(row[0]) if len(row)==1 else int(row[0]+row[1],16)
                elif line.startswith('Last checkpoint at'):
                    # Last checkpoint at  125 3934293461
                    # Last checkpoint at  1663926
                    row=[i for i in re.findall('Last checkpoint at  (\w+)(?: \w+)',line)[0] if len(i)>0]
                    status['last_checkpoint']=int(row[0]) if len(row)==1 else int(row[0]+row[1],16)
                # BUFFER POOL AND MEMORY
                elif line.startswith('Total memory allocated'):
                    #Total memory allocated 2146304000; in additional pool allocated 0
                    row=[int(i) for i in re.findall('Total memory allocated (\d+)(?:; in additional pool allocated (\d+))?',line)[0] if len(i)>0]
                    status['total_mem_alloc']=row[0]
                    if len(row)==2: status['additional_pool_alloc']=row[1]
                elif line.startswith('Adaptive hash index '):
                    #   Adaptive hash index 1538240664 	(186998824 + 1351241840)
                    row=[int(i) for i in re.findall('Adaptive hash index (\d+)',line) if len(i)>0]
                    status['adaptive_hash_memory']=row[0]
                elif line.startswith('Page hash           '):
                    #   Page hash           11688584
                    row=[int(i) for i in re.findall('Page hash           (\d+)',line) if len(i)>0]
                    status['page_hash_memory']=row[0]
                elif line.startswith('Dictionary cache    '):
                    #   Dictionary cache    145525560 	(140250984 + 5274576)
                    row=[int(i) for i in re.findall('Dictionary cache    (\d+)',line) if len(i)>0]
                    status['dictionary_cache_memory']=row[0]
                elif line.startswith('File system         '):
                    #   File system         313848 	(82672 + 231176)
                    row=[int(i) for i in re.findall('File system         (\d+)',line) if len(i)>0]
                    status['file_system_memory']=row[0]
                elif line.startswith('Lock system         '):
                    #   Lock system         29232616 	(29219368 + 13248)
                    row=[int(i) for i in re.findall('Lock system\s+(\d+)',line) if len(i)>0]
                    status['lock_system_memory']=row[2]
                elif line.startswith('Recovery system     '):
                    #   Recovery system     0 	(0 + 0)
                    row=[int(i) for i in re.findall('Recovery system\s+(\d+)',line) if len(i)>0]
                    status['recovery_system_memory']=row[0]
                elif line.startswith('Threads             '):
                    #   Threads             409336 	(406936 + 2400)
                    row=[int(i) for i in re.findall('Threads             (\d+)',line)[0] if len(i)>0]
                    status['thread_hash_memory']=row[0]
                elif line.startswith('innodb_io_pattern   '):
                    #   innodb_io_pattern   0 	(0 + 0)
                    row=[int(i) for i in re.findall('innodb_io_pattern   (\d+)',line)[0] if len(i)>0]
                    status['innodb_io_pattern_memory']=row[0]
                elif line.startswith('Buffer pool size '):
                    # The " " after size is necessary to avoid matching the wrong line:
                    # Buffer pool size        1769471
                    # Buffer pool size, bytes 28991012864
                    row=[int (i) for i in re.findall('Buffer pool size        (\d+)',line) if len(i)>0]
                    status['pool_size']=row[0]
                elif line.startswith('Free buffers'):
                    # Free buffers            0
                    row=[int(i) for i in re.findall('Free buffers            (\d+)',line) if len(i)>0]
                    status['free_pages']=row[0]
                elif line.startswith('Database pages'):
                    # Database pages          1696503
                    row=[int(i) for i in re.findall('Database pages          (\d+)',line) if len(i)>0]
                    status['database_pages']=row[0]
                elif line.startswith('Modified db pages'):
                    # Modified db pages       160602
                    row=[int(i) for i in re.findall('Modified db pages       (\d+)',line) if len(i)>0]
                    status['modified_pages']=row[0]
                elif line.startswith('Pages read ahead'):
                    # Must do this BEFORE the next test, otherwise it'll get fooled by this
                    # line from the new plugin (see samples/innodb-015.txt):
                    # Pages read ahead 0.00/s, evicted without access 0.06/s
                    # TODO: No-op for now, see issue 134.
                    pass
                elif line.startswith('Pages read'):
                    # Pages read 15240822, created 1770238, written 21705836
                    row=[int(i) for i in re.findall('Pages read (\d+), created (\d+), written (\d+)',line)[0] if len(i)>0]
                    status['pages_read']=row[0]
                    status['pages_created']=row[1]
                    status['pages_written']=row[2]
                # ROW OPERATIONS
                elif line.startswith('Number of rows inserted'):
                    # Number of rows inserted 50678311, updated 66425915, deleted 20605903, read 454561562
                    row=[int(i) for i in re.findall('Number of rows inserted (\d+), updated (\d+), deleted (\d+), read (\d+)',line)[0] if len(i)>0]
                    status['rows_inserted']=row[0]
                    status['rows_updated']=row[0]
                    status['rows_deleted']=row[0]
                    status['rows_read']=row[0]
                elif line.find(' queries inside InnoDB, ') != -1:
                    # 0 queries inside InnoDB, 0 queries in queue
                    row=[int(i) for i in re.findall('(\d+) queries inside InnoDB, (\d+) queries in queue',line)[0] if len(i)>0]
                    status['queries_inside']=row[0]
                    status['queries_queued']=row[1]
                #
                prev_line=line
            except Exception as e:
                traceback.format_exc()
                print e.message

        status['spin_waits'],status['spin_rounds'],status['os_waits'] = map(lambda x: sum(x),
                                                                        [status['spin_waits'],
                                                                        status['spin_rounds'],
                                                                        status['os_waits']])
        status['unflushed_log']=status['log_bytes_written']-status['log_bytes_flushed']
        status['uncheckpointed_bytes']=status['log_bytes_written']-status['last_checkpoint']
        return status
    @classmethod
    def _run_query(cls,query,conn,cursor=Cursor):
        try:
            cur=conn.cursor(cursor)
            count=cur.execute(query)
            result=cur.fetchall()
        except Exception as e:
            print e.message
        finally:
            cur.close()
            return result
    @classmethod
    def get_data(cls,host=None,port=None,user=None,passwd=None):
        conn=None
        try:
            status={
                # Holds the result of SHOW STATUS, SHOW INNODB STATUS, etc
                # Define some indexes so they don't cause errors with += operations.
                'relay_log_space'            : None,
                'binary_log_space'           : None,
                'current_transactions'       : 0,
                'locked_transactions'        : 0,
                'active_transactions'        : 0,
                'innodb_locked_tables'       : 0,
                'innodb_tables_in_use'       : 0,
                'innodb_lock_structs'        : 0,
                'innodb_lock_wait_secs'      : 0,
                'innodb_sem_waits'           : 0,
                'innodb_sem_wait_time_ms'    : 0,                
                # Values for the 'state' column from SHOW PROCESSLIST (converted to
                # lowercase, with spaces replaced by underscores)                
                'State_closing_tables'       : 0,
                'State_copying_to_tmp_table' : 0,
                'State_end'                  : 0,
                'State_freeing_items'        : 0,
                'State_init'                 : 0,
                'State_locked'               : 0,
                'State_login'                : 0,
                'State_preparing'            : 0,
                'State_reading_from_net'     : 0,
                'State_sending_data'         : 0,
                'State_sorting_result'       : 0,
                'State_statistics'           : 0,
                'State_updating'             : 0,
                'State_writing_to_net'       : 0,
                'State_none'                 : 0,
                'State_other'                : 0, # Everything not listed above                
            }
            conn=MySQLdb.connect(host=host,port=port,user=user,passwd=passwd)
            conn.cursor()
            res=cls._run_query("SHOW /*!50002 GLOBAL */ STATUS",conn)
            if res and len(res)>0:
                status.update(dict(res))
            res=cls._run_query("SHOW VARIABLES",conn)
            if res and len(res)>0:
                status.update(dict(res))
            res=cls._run_query("show slave status",conn,DictCursor)
            if res and len(res)>0:
                status.update(res[0])
                status['slave_running']=status['slave_lag'] if status['slave_sql_running'] == 'YES' else 0
                status['slave_stopped']=0 if status['slave_sql_running'] else status['slave_lag']
            res=cls._run_query("SHOW MASTER LOGS",conn)
            if res and len(res)>0:
                status['binary_log_space']=sum([i[1] for i in res])
            res=cls._run_query("SHOW PROCESSLIST",conn,DictCursor)
            if res and len(res)>0:
                for row in res:
                    state=row['State']
                    if state is None or state == '': continue
                    state=re.sub('^Table lock|Waiting for .*lock$','locked',state)
                    if status.has_key('State_%s' % state):
                        status['State_%s' % state]+=1
                    else:
                        status['State_other']+=1
            engines={}
            res=cls._run_query("SHOW ENGINES",conn)
            if res and len(res)>0:
                engines.update(dict([i[:2] for i in res]))
            if engines.has_key('InnoDB') and engines['InnoDB'] in ('YES','DEFAULT'):
                res=cls._run_query("SHOW /*!50000 ENGINE*/ INNODB STATUS",conn,DictCursor)
                if res and len(res)>0:
                    innodb_status=cls.get_innodb_status(res[0]['Status'])
                    overrides={
                        'Innodb_buffer_pool_pages_data'  : 'database_pages',
                        'Innodb_buffer_pool_pages_dirty' : 'modified_pages',
                        'Innodb_buffer_pool_pages_free'  : 'free_pages',
                        'Innodb_buffer_pool_pages_total' : 'pool_size',
                        'Innodb_data_fsyncs'             : 'file_fsyncs',
                        'Innodb_data_pending_reads'      : 'pending_normal_aio_reads',
                        'Innodb_data_pending_writes'     : 'pending_normal_aio_writes',
                        'Innodb_os_log_pending_fsyncs'   : 'pending_log_flushes',
                        'Innodb_pages_created'           : 'pages_created',
                        'Innodb_pages_read'              : 'pages_read',
                        'Innodb_pages_written'           : 'pages_written',
                        'Innodb_rows_deleted'            : 'rows_deleted',
                        'Innodb_rows_inserted'           : 'rows_inserted',
                        'Innodb_rows_read'               : 'rows_read',
                        'Innodb_rows_updated'            : 'rows_updated',
                        'Innodb_buffer_pool_reads'       : 'pool_reads',
                        'Innodb_buffer_pool_read_requests' : 'pool_read_requests',                        
                    }
                    for key in overrides.keys():
                        if status.has_key(key):
                            innodb_status[overrides[key]]=status[key]
                    status.update(innodb_status)
            # Get response time histogram from Percona Server or MariaDB if enabled.
            if (status.has_key('have_response_time_distribution') and status['have_response_time_distribution']=='YES') \
               or ((status.has_key('query_response_time_stats') and status['query_response_time_stats'])):
                res=cls._run_query("SELECT `count`, ROUND(total * 1000000) AS total FROM INFORMATION_SCHEMA.QUERY_RESPONSE_TIME WHERE `time` <> 'TOO LONG'",conn)
                if res and len(res)>0:
                    rn=len(res)
                    for offset in range(13):
                        item=res[offset] if offset < rn else [0,0]
                        status["Query_time_count_%02d" % offset]=item[0]
                        status["Query_time_total_%02d" % offset]=item[1]
            # Make table_open_cache backwards-compatible (issue 63).
            if status.has_key('table_open_cache'):
                status['table_cache']=status['table_open_cache']
            # Compute how much of the key buffer is used and unflushed (issue 127).
            status['Key_buf_bytes_used']=status['key_buffer_size']-(status['Key_blocks_unused']*status['key_cache_block_size'])
            status['Key_buf_bytes_unflushed']=status['Key_blocks_not_flushed']*status['key_cache_block_size']
            if status.has_key('unflushed_log') and status['unflushed_log']:
                # TODO: I'm not sure what the deal is here; need to debug this.  But the
                # unflushed log bytes spikes a lot sometimes and it's impossible for it to
                # be more than the log buffer.                
                status['unflushed_log']=max([status['unflushed_log'],status['innodb_log_buffer_size']])
            return status
        except Exception as e:
            traceback.format_exc()
            print e
        finally:
            if conn: conn.close()
            return status

if __name__ == "__main__":
    import  json
    st=json.dumps(MySQL_Monitor.get_data(host=sys.argv[1],port=int(sys.argv[2]),user=sys.argv[3],passwd=sys.argv[4]),indent=4)
    print st