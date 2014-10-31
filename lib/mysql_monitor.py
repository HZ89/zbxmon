#!/opt/17173_install/python-2.7.6/bin/python2.7
# coding:utf-8
__author__ = 'Justin Ma'
__verion__ = '0.5.0'
import os, sys
import string
import re
import MySQLdb
import traceback
from MySQLdb.cursors import Cursor, DictCursor

# http://www.percona.com/doc/percona-monitoring-plugins/1.0/cacti/mysql-templates.html

class MySQL_Monitor(object):
    @classmethod
    def _get_innodb_status(cls, text):
        """
        analyze the output into innodb performance  when run command of  'show engine innodb status'
        :param text: a string of command output
        :return: a dict with innodb status
        """
        status = {
            'spin_waits': [],
            'spin_rounds': [],
            'os_waits': [],
            'pending_normal_aio_reads': 0,
            'pending_normal_aio_writes': 0,
            'pending_ibuf_aio_reads': 0,
            'pending_aio_log_ios': 0,
            'pending_aio_sync_ios': 0,
            'pending_log_flushes': 0,
            'pending_buf_pool_flushes': 0,
            'file_reads': 0,
            'file_writes': 0,
            'file_fsyncs': 0,
            'ibuf_inserts': 0,
            'ibuf_merged': 0,
            'ibuf_merges': 0,
            'log_bytes_written': 0,
            'unflushed_log': 0,
            'log_bytes_flushed': 0,
            'pending_log_writes': 0,
            'pending_chkp_writes': 0,
            'log_writes': 0,
            'pool_size': 0,
            'free_pages': 0,
            'database_pages': 0,
            'modified_pages': 0,
            'pages_read': 0,
            'pages_created': 0,
            'pages_written': 0,
            'queries_inside': 0,
            'queries_queued': 0,
            'read_views': 0,
            'rows_inserted': 0,
            'rows_updated': 0,
            'rows_deleted': 0,
            'rows_read': 0,
            'innodb_transactions': 0,
            'unpurged_txns': 0,
            'history_list': 0,
            'current_transactions': 0,
            'active_transactions': 0,
            'hash_index_cells_total': 0,
            'hash_index_cells_used': 0,
            'total_mem_alloc': 0,
            'additional_pool_alloc': 0,
            'last_checkpoint': 0,
            'uncheckpointed_bytes': 0,
            'ibuf_used_cells': 0,
            'ibuf_free_cells': 0,
            'ibuf_cell_count': 0,
            'adaptive_hash_memory': 0,
            'page_hash_memory': 0,
            'dictionary_cache_memory': 0,
            'file_system_memory': 0,
            'lock_system_memory': 0,
            'recovery_system_memory': 0,
            'thread_hash_memory': 0,
            'innodb_sem_waits': 0,
            'innodb_sem_wait_time_ms': 0,
            'innodb_lock_wait_secs': 0,
            'innodb_tables_in_use': 0,
            'innodb_locked_tables': 0,
            'innodb_lock_structs': 0,
            'locked_transactions': 0,
            'innodb_io_pattern_memory': 0,
        }
        txn_seen = False
        line = ''
        prev_line = ''
        for line in string.split(text, '\n'):
            line = string.strip(line)
            if line == '': continue
            row = None
            try:
                #SEMAPHORES
                if line.startswith('Mutex spin waits'):
                    # Mutex spin waits 79626940, rounds 157459864, OS waits 698719
                    row = [int(i) for i in
                           re.findall('Mutex spin waits\s+(\d+), rounds\s+(\d+),\s*OS waits\s+(\d+)', line)[0]
                           if len(i) > 0]
                    status['spin_waits'].append(row[0])
                    status['spin_rounds'].append(row[1])
                    status['os_waits'].append(row[2])
                elif line.startswith('RW-shared spins'):
                    # RW-shared spins 3859028, OS waits 2100750; RW-excl spins 4641946, OS waits 1530310
                    # Post 5.5.17 SHOW ENGINE INNODB STATUS syntax
                    # RW-shared spins 604733, rounds 8107431, OS waits 241268
                    row = [int(i) for i in
                           re.findall('RW-shared spins\s+(\d+),(?:\s*rounds\s+(\d+),)? OS waits\s+(\d+)', line)[0] if
                           len(i) > 0]
                    if len(row) == 3:  row.pop(1)
                    status['spin_waits'].append(row[0])
                    status['os_waits'].append(row[1])
                elif line.find('RW-excl spins') != -1:
                    # RW-shared spins 3859028, OS waits 2100750; RW-excl spins 4641946, OS waits 1530310
                    # Post 5.5.17 SHOW ENGINE INNODB STATUS syntax
                    # RW-excl spins 604733, rounds 8107431, OS waits 241268
                    row = [int(i) for i in
                           re.findall('RW-excl spins\s+(\d+),(?: rounds\s+(\d+),)? OS waits\s+(\d+)', line)[0]
                           if len(i) > 0]
                    if len(row) == 3:  row.pop(1)
                    status['spin_waits'].append(row[0])
                    status['os_waits'].append(row[1])
                elif line.find('seconds the semaphore:') != -1:
                    # --Thread 907205 has waited at handler/ha_innodb.cc line 7156 for 1.00 seconds the semaphore:
                    status['innodb_sem_waits'] += 1
                    row = re.findall('for\s+(\d+.\d+) seconds the semaphore:', line)[0]
                    status['innodb_sem_wait_time_ms'] += float(row[0]) * 1000
                #TRANSACTIONS
                elif line.startswith('Trx id counter'):
                    # The beginning of the TRANSACTIONS section: start counting
                    # transactions
                    # Trx id counter 0 1170664159
                    # Trx id counter 861B144C
                    row = [i for i in re.findall('Trx id counter(?: (\d+))?\s+(\w+)', line)[0] if len(i) > 0]
                    status['innodb_transactions'] = int(row[0] if len(row) == 1 else row[0] + row[1], 16)
                    txn_seen = True
                elif line.startswith('Purge done for trx'):
                    # Purge done for trx's n:o < 0 1170663853 undo n:o < 0 0
                    # Purge done for trx's n:o < 861B135D undo n:o < 0
                    row = [i for i in
                           re.findall('''Purge done for trx's n:o <(?: (\w+))?\s+(\w+) undo n:o <''', line)[0]
                           if len(i) > 0]
                    status['unpurged_txns'] = status['innodb_transactions'] - int(
                        row[0] if len(row) == 1 else row[0] + row[1], 16)
                elif line.startswith('History list length'):
                    #History list length 1557
                    row = re.findall('History list length\s+(\d+)', line)
                    status['history_list'] = int(row[0])
                elif txn_seen and line.startswith('---TRANSACTION'):
                    # ---TRANSACTION 0, not started, process no 13510, OS thread id 1170446656
                    #---TRANSACTION 6D8BB4768, not started
                    status['current_transactions'] += 1
                    if line.find('ACTIVE') != -1: status['active_transactions'] += 1
                elif txn_seen and line.startswith('------- TRX HAS BEEN'):
                    # ------- TRX HAS BEEN WAITING 32 SEC FOR THIS LOCK TO BE GRANTED:
                    row = re.findall('TRX HAS BEEN WAITING\s+(\d+)\s+SEC FOR THIS LOCK TO BE GRANTED', line)
                    status['innodb_lock_wait_secs'] += int(row[0])
                elif line.find('read views open inside InnoDB') != -1:
                    # 1 read views open inside InnoDB
                    row = re.findall('(\d+)\s+read views open inside InnoDB', line)
                    status['read_views'] += int(row[0])
                elif line.startswith('mysql tables in use'):
                    # mysql tables in use 2, locked 2
                    row = re.findall('mysql tables in use\s+(\d+), locked\s+(\d+)', line)[0]
                    status['innodb_tables_in_use'] += int(row[0])
                    status['innodb_locked_tables'] += int(row[1])
                elif txn_seen and line.find('lock struct(s)') != -1:
                    # 23 lock struct(s), heap size 3024, undo log entries 27
                    # LOCK WAIT 12 lock struct(s), heap size 3024, undo log entries 5
                    row = re.findall('(\d+)\s+lock struct\(s\)', line)[0]
                    status['innodb_lock_structs'] += int(row)
                    if line.startswith('LOCK WAIT'):
                        status['locked_transactions'] += int(row)
                # FILE I/O
                elif line.find(' OS file reads, ') != -1:
                    # 8782182 OS file reads, 15635445 OS file writes, 947800 OS fsyncs
                    row = re.findall('(\d+) OS file reads,\s+(\d+) OS file writes,\s+(\d+) OS fsyncs', line)[0]
                    status['file_reads'] = int(row[0])
                    status['file_writes'] = int(row[1])
                    status['file_fsyncs'] = int(row[2])
                elif line.startswith('Pending normal aio reads:'):
                    # Pending normal aio reads: 0, aio writes: 0,
                    row = re.findall('Pending normal aio reads:\s+(\d+).*, aio writes:\s+(\d+).*,', line)[0]
                    status['pending_normal_aio_reads'] = int(row[0])
                    status['pending_normal_aio_writes'] = int(row[1])
                elif line.startswith('ibuf aio reads'):
                    #  ibuf aio reads: 0, log i/o's: 0, sync i/o's: 0
                    row = re.findall('''ibuf aio reads:\s+(\d+), log i/o's:\s+(\d+), sync i/o's:\s+(\d+)''', line)[0]
                    status['pending_ibuf_aio_reads'] = int(row[0])
                    status['pending_aio_log_ios'] = int(row[1])
                    status['pending_aio_sync_ios'] = int(row[2])
                elif line.startswith('Pending flushes (fsync)'):
                    # Pending flushes (fsync) log: 0; buffer pool: 0
                    row = re.findall('Pending flushes \(fsync\) log:\s+(\d+); buffer pool:\s+(\d+)', line)[0]
                    status['pending_log_flushes'] = int(row[0])
                    status['pending_buf_pool_flushes'] = int(row[1])
                # INSERT BUFFER AND ADAPTIVE HASH INDEX
                elif line.startswith('Ibuf for space 0: size '):
                    # Older InnoDB code seemed to be ready for an ibuf per tablespace.  It
                    # had two lines in the output.  Newer has just one line, see below.
                    # Ibuf for space 0: size 1, free list len 887, seg size 889, is not empty
                    # Ibuf for space 0: size 1, free list len 887, seg size 889,
                    row = re.findall('Ibuf for space 0: size\s+(\d+), free list len\s+(\d+), seg size\s+(\d+)', line)[0]
                    status['ibuf_used_cells'] = int(row[0])
                    status['ibuf_free_cells'] = int(row[1])
                    status['ibuf_cell_count'] = int(row[2])
                elif line.startswith('Ibuf: size '):
                    # Ibuf: size 1, free list len 4634, seg size 4636,
                    #Ibuf: size 1, free list len 11, seg size 13, 17 merges
                    row = [i for i in
                           re.findall('Ibuf: size\s+(\d+), free list len\s+(\d+), seg size\s+(\d+),(?: (\d+) merges)?',
                                      line)[
                               0] if len(i) > 0]
                    status['ibuf_used_cells'] = int(row[0])
                    status['ibuf_free_cells'] = int(row[1])
                    status['ibuf_cell_count'] = int(row[2])
                    if len(row) == 4:
                        status['ibuf_merged'] = int(row[3])
                elif line.find(', delete mark ') != -1 and prev_line.startswith('merged operations:'):
                    # Output of show engine innodb status has changed in 5.5
                    # merged operations:
                    # insert 593983, delete mark 387006, delete 73092
                    row = re.findall('insert\s+(\d+), delete mark\s+(\d+), delete\s+(\d+)', line)[0]
                    status['ibuf_inserts'] = int(row[0])
                    status['ibuf_merged'] = int(row[0]) + int(row[1]) + int(row[2])
                elif line.find(' merged recs, ') != -1:
                    # 19817685 inserts, 19817684 merged recs, 3552620 merges
                    row = [int(i) for i in re.findall('(d+) inserts,\s+(\d+) merged recs,\s+(\d+) merges', line)[0]]
                    status['ibuf_inserts'] = row[0]
                    status['ibuf_merged'] = row[1]
                    status['ibuf_merges'] = row[2]
                elif line.startswith('Hash table size '):
                    # In some versions of InnoDB, the used cells is omitted.
                    # Hash table size 4425293, used cells 4229064, ....
                    # Hash table size 57374437, node heap has 72964 buffer(s) <-- no used cells
                    row = [int(i) for i in re.findall('Hash table size\s+(\d+),(?: used cells\s+(\d+))?', line)[0] if
                           len(i) > 0]
                    status['hash_index_cells_total'] = row[0]
                    if len(row) == 2:
                        status['hash_index_cells_used'] = row[1]
                # LOG
                elif line.find(''' log i/o's done, ''') != -1:
                    # 3430041 log i/o's done, 17.44 log i/o's/second
                    # 520835887 log i/o's done, 17.28 log i/o's/second, 518724686 syncs, 2980893 checkpoints
                    # TODO: graph syncs and checkpoints
                    row = re.findall("(\d+) log i/o's done", line)
                    status['log_writes'] = int(row[0])
                elif line.find(' pending log writes, ') != -1:
                    # 0 pending log writes, 0 pending chkp writes
                    row = [int(i) for i in
                           re.findall('(\d+)\s+pending log writes, (\d+)\s+pending chkp writes', line)[0]]
                    status['pending_log_writes'] = row[0]
                    status['pending_chkp_writes'] = row[1]
                elif line.startswith('Log sequence number'):
                    # This number is NOT printed in hex in InnoDB plugin.
                    # Log sequence number 13093949495856 //plugin
                    # Log sequence number 125 3934414864 //normal
                    row = [i for i in re.findall('Log sequence number\s+(\w+)(?: (\w+))?', line)[0] if len(i) > 0]
                    status['log_bytes_written'] = int(row[0]) if len(row) == 1 else int(row[0] + row[1], 16)
                elif line.startswith('Log flushed up to'):
                    # This number is NOT printed in hex in InnoDB plugin.
                    # Log flushed up to   13093948219327
                    # Log flushed up to   125 3934414864
                    row = [i for i in re.findall('Log flushed up to\s+(\w+)(?: (\w+))?', line)[0] if len(i) > 0]
                    status['log_bytes_flushed'] = int(row[0]) if len(row) == 1 else int(row[0] + row[1], 16)
                elif line.startswith('Last checkpoint at'):
                    # Last checkpoint at  125 3934293461
                    # Last checkpoint at  1663926
                    row = [i for i in re.findall('Last checkpoint at\s+(\w+)(?: \w+)?', line)[0] if len(i) > 0]
                    status['last_checkpoint'] = int(row[0]) if len(row) == 1 else int(row[0] + row[1], 16)
                # BUFFER POOL AND MEMORY
                elif line.startswith('Total memory allocated'):
                    #Total memory allocated 2146304000; in additional pool allocated 0
                    row = [int(i) for i in
                           re.findall('Total memory allocated\s+(\d+)(?:; in additional pool allocated\s+(\d+))?',
                                      line)[0]
                           if len(i) > 0]
                    status['total_mem_alloc'] = row[0]
                    if len(row) == 2: status['additional_pool_alloc'] = row[1]
                elif line.startswith('Adaptive hash index '):
                    #   Adaptive hash index 1538240664 	(186998824 + 1351241840)
                    row = [int(i) for i in re.findall('Adaptive hash index\s+(\d+)', line) if len(i) > 0]
                    status['adaptive_hash_memory'] = row[0]
                elif line.startswith('Page hash           '):
                    #   Page hash           11688584
                    row = [int(i) for i in re.findall('Page hash\s+(\d+)', line) if len(i) > 0]
                    status['page_hash_memory'] = row[0]
                elif line.startswith('Dictionary cache    '):
                    #   Dictionary cache    145525560 	(140250984 + 5274576)
                    row = [int(i) for i in re.findall('Dictionary cache\s+(\d+)', line) if len(i) > 0]
                    status['dictionary_cache_memory'] = row[0]
                elif line.startswith('File system         '):
                    #   File system         313848 	(82672 + 231176)
                    row = [int(i) for i in re.findall('File system\s+(\d+)', line) if len(i) > 0]
                    status['file_system_memory'] = row[0]
                elif line.startswith('Lock system         '):
                    #   Lock system         29232616 	(29219368 + 13248)
                    row = [int(i) for i in re.findall('Lock system\s+(\d+)', line) if len(i) > 0]
                    status['lock_system_memory'] = row[0]
                elif line.startswith('Recovery system     '):
                    #   Recovery system     0 	(0 + 0)
                    row = [int(i) for i in re.findall('Recovery system\s+(\d+)', line) if len(i) > 0]
                    status['recovery_system_memory'] = row[0]
                elif line.startswith('Threads             '):
                    #   Threads             409336 	(406936 + 2400)
                    row = [int(i) for i in re.findall('Threads\s+(\d+)', line)[0] if len(i) > 0]
                    status['thread_hash_memory'] = row[0]
                elif line.startswith('innodb_io_pattern   '):
                    #   innodb_io_pattern   0 	(0 + 0)
                    row = [int(i) for i in re.findall('innodb_io_pattern\s+(\d+)', line)[0] if len(i) > 0]
                    status['innodb_io_pattern_memory'] = row[0]
                elif line.startswith('Buffer pool size '):
                    # The " " after size is necessary to avoid matching the wrong line:
                    # Buffer pool size        1769471
                    # Buffer pool size, bytes 28991012864
                    row = [int(i) for i in re.findall('Buffer pool size\s+(\d+)', line) if len(i) > 0]
                    status['pool_size'] = row[0]
                elif line.startswith('Free buffers'):
                    # Free buffers            0
                    row = [int(i) for i in re.findall('Free buffers\s+(\d+)', line) if len(i) > 0]
                    status['free_pages'] = row[0]
                elif line.startswith('Database pages'):
                    # Database pages          1696503
                    row = [int(i) for i in re.findall('Database pages\s+(\d+)', line) if len(i) > 0]
                    status['database_pages'] = row[0]
                elif line.startswith('Modified db pages'):
                    # Modified db pages       160602
                    row = [int(i) for i in re.findall('Modified db pages\s+(\d+)', line) if len(i) > 0]
                    status['modified_pages'] = row[0]
                elif line.startswith('Pages read ahead'):
                    # Must do this BEFORE the next test, otherwise it'll get fooled by this
                    # line from the new plugin (see samples/innodb-015.txt):
                    # Pages read ahead 0.00/s, evicted without access 0.06/s
                    # TODO: No-op for now, see issue 134.
                    pass
                elif line.startswith('Pages read'):
                    # Pages read 15240822, created 1770238, written 21705836
                    row = [int(i) for i in re.findall('Pages read\s+(\d+), created\s+(\d+), written\s+(\d+)', line)[0]
                           if
                           len(i) > 0]
                    status['pages_read'] = row[0]
                    status['pages_created'] = row[1]
                    status['pages_written'] = row[2]
                # ROW OPERATIONS
                elif line.startswith('Number of rows inserted'):
                    # Number of rows inserted 50678311, updated 66425915, deleted 20605903, read 454561562
                    row = [int(i) for i in
                           re.findall('Number of rows inserted\s+(\d+), updated\s+(\d+), deleted\s+(\d+), read\s+(\d+)',
                                      line)[
                               0] if len(i) > 0]
                    status['rows_inserted'] = row[0]
                    status['rows_updated'] = row[0]
                    status['rows_deleted'] = row[0]
                    status['rows_read'] = row[0]
                elif line.find(' queries inside InnoDB, ') != -1:
                    # 0 queries inside InnoDB, 0 queries in queue
                    row = [int(i) for i in
                           re.findall('(\d+)\s+queries inside InnoDB, (\d+)\s+queries in queue', line)[0] if
                           len(i) > 0]
                    status['queries_inside'] = row[0]
                    status['queries_queued'] = row[1]
                #
                prev_line = line
            except Exception as e:
                traceback.print_exc()
                print e.message
        cls._change_dict_value_to_int(status)
        status['spin_waits'], status['spin_rounds'], status['os_waits'] = map(lambda x: sum(x),
                                                                              [status['spin_waits'],
                                                                               status['spin_rounds'],
                                                                               status['os_waits']])
        status['unflushed_log'] = status['log_bytes_written'] - status['log_bytes_flushed']
        status['uncheckpointed_bytes'] = status['log_bytes_written'] - status['last_checkpoint']
        return status

    @classmethod
    def _run_query(cls, query, conn, cursor=Cursor):
        '''
        exceute SQL query using a mysql connection and return the result
        :param query: the SQL sentence
        :param conn: an object  returned by MySQLdb.connect()
        :param cursor: choice from MySQL.cursors.Cursor and MySQL.cursors.DictCursor
        :return: query result list, the item is list when cursor used Cursor, or dict when cursor used DictCursor
        '''
        result=None
        try:
            cur = conn.cursor(cursor)
            count = cur.execute(query)
            result = cur.fetchall()
        except Exception as e:
            traceback.print_exc()
            print e.message
        finally:
            cur.close()
        return result

    @classmethod
    def _change_dict_value_to_int(cls, target):
        if type(target) is not dict: return
        for key in target.keys():
            if type(target[key]) is str and target[key].isdigit():
                target[key] = int(target[key])
        return target

    @classmethod
    def mysql_ping(cls, host, port, user, passwd):
        result = 0
        conn = None
        try:
            conn = MySQLdb.connect(host=host, port=port, user=user, passwd=passwd)
            conn.ping()
        except (MySQLdb.MySQLError, MySQLdb.Error, MySQLdb.InterfaceError, MySQLdb.NotSupportedError, Exception) as e:
            #print e.message
            # operationerror: not allowed to connect
            result = -1
        finally:
            if conn: conn.close()
        return result

    @classmethod
    def grant_monitor_user(self, socket, user, host, passwd):
        result = 0
        conn = None
        cur = None
        try:
            conn = MySQLdb.connect(unix_socket=socket)
            cur = conn.cursor()
            # MySQL Community Server (GPL) 5.5.24-log  needed super privilges
            count = cur.execute(
                "GRANT SUPER,PROCESS,REPLICATION CLIENT ON *.* to '%s'@'%s' identified by '%s' WITH MAX_USER_CONNECTIONS 5;flush privileges" % (
                user, host, passwd))
            result = 1
        except (MySQLdb.MySQLError, MySQLdb.Error, MySQLdb.InterfaceError, MySQLdb.NotSupportedError) as e:
            print e
            result = -1
        except MySQLdb.OperationalError as e:
            result = -2
            print e
        finally:
            if cur: cur.close()
            if conn: conn.close()
        return result

    @classmethod
    def get_monitor_data(cls, host=None, port=None, user=None, passwd=None, socket=None):
        '''
        collect performance data from a mysql instance.
        the method is Modeled after Percona monitor plugin.
        to be the operation, need to gived the privileges:
            PROCESS
            REPLICATION CLIENT
        :param host: monitored server address
        :param port: monitored mysql listen port
        :param user: login user name
        :param passwd: login password
        :return: a dict with the mysql instance performace data
        '''
        conn = None
        try:
            if socket:
                conn = MySQLdb.connect(unix_socket=socket)
            else:
                conn = MySQLdb.connect(host=host, port=int(port), user=user, passwd=passwd)
        except (MySQLdb.MySQLError, MySQLdb.DatabaseError, MySQLdb.Error) as e:
            traceback.print_exc()
            print e.message
            return {}
        except Exception as e:
            traceback.print_exc()
            print e.message
            return {}
        try:
            status = {
                # Holds the result of SHOW STATUS, SHOW INNODB STATUS, etc
                # Define some indexes so they don't cause errors with += operations.
                'relay_log_space': None,
                'binary_log_space': None,
                'current_transactions': 0,
                'locked_transactions': 0,
                'active_transactions': 0,
                'innodb_locked_tables': 0,
                'innodb_tables_in_use': 0,
                'innodb_lock_structs': 0,
                'innodb_lock_wait_secs': 0,
                'innodb_sem_waits': 0,
                'innodb_sem_wait_time_ms': 0,
                # Values for the 'state' column from SHOW PROCESSLIST (converted to
                # lowercase, with spaces replaced by underscores)
                'State_closing_tables': 0,
                'State_copying_to_tmp_table': 0,
                'State_end': 0,
                'State_freeing_items': 0,
                'State_init': 0,
                'State_locked': 0,
                'State_login': 0,
                'State_preparing': 0,
                'State_reading_from_net': 0,
                'State_sending_data': 0,
                'State_sorting_result': 0,
                'State_statistics': 0,
                'State_updating': 0,
                'State_writing_to_net': 0,
                'State_none': 0,
                'State_other': 0,  # Everything not listed above
            }

            conn.cursor()
            res = cls._run_query("SHOW /*!50002 GLOBAL */ STATUS", conn)
            if res and len(res) > 0:
                status.update(cls._change_dict_value_to_int(dict(res)))
            res = cls._run_query("SHOW VARIABLES", conn)
            if res and len(res) > 0:
                status.update(cls._change_dict_value_to_int(dict(res)))

            #thread cache hit rate
            status['thread_cache_hit_rate']=(1-float(status.get('Threads_created',0)/status.get('Connections',0)))*100.0
            # WARNING : < 95% CRITICAL : < 90%
            status['thread_connected_rate']=float(status.get('Threads_connected',0))/status.get('max_connections',1)*100.0
            # key buffer miss rate
            # 0.1%以下都很好(每1000个请求有一个直接读硬盘)
            # 在0.01%以下的话，key_buffer_size分配的过多，可以适当减少
            status['key_buffer_hit_rate']=(1-float(status.get('Key_reads',0))/status.get('Key_read_requests',1))*100.0
            # key block used ratio Key_blocks_used
            # Key_blocks_unused表示未使用的缓存簇(blocks)数，Key_blocks_used表示曾经用到的最大的blocks数，
            # 比如这台服务器，所有的缓存都用到了，要么增加key_buffer_size，要么就是过渡索引了，把缓存占满了
            # 比较理想的设置: ≈ 80%
            status['key_block_used_rate']=float(status.get('Key_blocks_used',0))/(status.get('Key_blocks_used',0)+status.get('Key_blocks_unused',1))*100
            # 磁盘上创建临时表的比例
            # 每次创建临时表，Created_tmp_tables增加，如果是在磁盘上创建临时表
            # Created_tmp_disk_tables也增加,Created_tmp_files表示MySQL服务创建的临时文件文件数
            # 比较理想的配置是 <= 25%
            status['created_tmp_disk_table_rate']=float(status.get('Created_tmp_disk_tables',0))/status.get('Created_tmp_tables',1)*100.0
            # 表缓存命中率
            # Open_tables表示打开表的数量，Opened_tables表示打开过的表数量，如果Opened_tables数量过大，
            # 说明配置中table_cache(5.1.3之后这个值叫做table_open_cache)值可能太小，我们查询一下服务器table_cache值
            # 比较合适: >= 85%
            status['open_table_hit_rate']=float(status.get('Open_tables',0))/status.get('Opened_tables',1)*100.0
            # 表缓存使用率
            # 首先判断使用率，如果使用率<95%则表示状态正常；假如使用率>=95%则开始判断命中率，命中率阀值判断如下：
            status['open_table_usage_rate']=float(status.get('Open_tables',0))/status.get('table_open_cache',1)*100.0
            # query cache fragment ratio
            # 如果查询缓存碎片率超过20%，可以用FLUSH QUERY CACHE整理缓存碎片
            status['qcache_fragment_rate']=float(status.get('Qcache_free_blocks',0))/status.get('Qcache_total_blocks',1)*100.0

            # query cache usage ratio
            # 查询缓存利用率在25%以下的话说明query_cache_size设置的过大，可适当减小;
            # 查询缓存利用率在80%以上而且Qcache_lowmem_prunes > 50的话说明query_cache_size可能有点小，要不就是碎片太多
            status['qcache_usage_rate']=float(status.get('query_cache_size',0)-status.get('Qcache_free_memory',0))/status.get('query_cache_size',1)*100

            # select query cache hits rate
            # mysql administrator: ([Qcache_hits]/([Qcache_hits]+[QCache_inserts]+[QCache_not_cached]))*100
            status['qcache_hit_rate']=float(status.get('Qcache_hits',0))/(status.get('Qcache_hits',1)+status.get('Qcache_inserts',0))*100.0

            # InnoDB缓存命中率
            # WARNING : < 95% CRITICAL : < 85%
            # 命中率太低说明innodb_buffer_pool_size设置太低，innodb_buffer_pool_size里面缓存了InnoDB引擎表的索引和数据，内存不足时查询只能从硬盘读取索引与数据，查询效率下降
            status['innodb_buffer_pool_hit_rate']=(1-float(status.get('Innodb_buffer_pool_reads',0))/status.get('Innodb_buffer_pool_read_requests',1))*100.0
            # 表扫描使用索引比例
            # 当发生故障告警时表示超过一半的查询请求不使用索引或者索引使用不正确。
            status['index_usage_rate']=(1-float(status.get('Handler_read_rnd',0))/status.get('Handler_read_first',1)
                                        +status.get('Handler_read_key',1)+status.get('Handler_read_next',1)+
                                        status.get('Handler_read_prev',1)+status.get('Handler_read_rnd',1)+
                                        status.get('Handler_read_rnd_next',1))*100.0
            # 发生表锁等待的次数比例
            # WARNING : > 10% CRITICAL : > 30%
            # 当发生告警说明表锁造成的阻塞比较严重，需要注意是否使用事务引擎吗，或者是注意是否发存在表扫描更新的情况
            status['table_lock_wait_rate']=float(status.get('Table_locks_waited',0))/status.get('Table_locks_immediate',1)*100.0

            # binlog日志缓存写在磁盘上的比例
            # WARNING : > 5% CRITICAL : > 10%
            # binlog_cache_size太小或者binlog生成太快，binlog缓存不够只能写在硬盘上。
            status['binlog_cache_disk_rate']=float(status.get('Binlog_stmt_cache_disk_use',0))/status.get('Binlog_cache_use',1)*100.0

            # slave-running
            # slave-lag
            # slave-stopped
            # slave-running
            # relay-log-space
            #
            status['slave_running']=status['slave_running']=='ON' and 1 or 0
            status['slave_sql_running']='NULL'
            status['slave_io_running']='NULL'
            status['slave_lag'] = 0
            status['relay_log_space'] = 0
            if status['slave_running'] == 1:
                res = cls._run_query("show slave status", conn, DictCursor)
                if res and len(res) > 0:
                    # Must lowercase keys because different MySQL versions have different lettercase.
                    slave_status = {key.lower(): val for key, val in res[0].iteritems()}
                    status.update(cls._change_dict_value_to_int(slave_status))
                    if status.get('slave_sql_running','NULL') != 'YES' or status.get('slave_io_running','NULL') == 'YES':
                        status['slave_running']=-1
                        status['slave_lag'] = 0
                    else:
                        status['slave_lag'] = status.get('seconds_behind_master',0)
            res = cls._run_query("SHOW MASTER LOGS", conn)
            if res and len(res) > 0:
                status['binary_log_space'] = sum([int(i[1]) for i in res])
            res = cls._run_query("SHOW PROCESSLIST", conn, DictCursor)
            if res and len(res) > 0:
                cls._change_dict_value_to_int(res)
                for row in res:
                    state = row['State']
                    if state is None or state == '': continue
                    state = re.sub('^Table lock|Waiting for .*lock$', 'locked', state)
                    if status.has_key('State_%s' % state):
                        status['State_%s' % state] += 1
                    else:
                        status['State_other'] += 1
            engines = {}
            res = cls._run_query("SHOW ENGINES", conn)
            if res and len(res) > 0:
                engines.update(dict([i[:2] for i in res]))
            if engines.has_key('InnoDB') and engines['InnoDB'] in ('YES', 'DEFAULT'):
                res = cls._run_query("SHOW /*!50000 ENGINE*/ INNODB STATUS", conn, DictCursor)
                if res and len(res) > 0:
                    innodb_status = cls._get_innodb_status(res[0]['Status'])
                    overrides = {
                        'Innodb_buffer_pool_pages_data':    ['database_pages',1],
                        'Innodb_buffer_pool_pages_dirty':   ['modified_pages',1],
                        'Innodb_buffer_pool_pages_free':    ['free_pages',1],
                        'Innodb_buffer_pool_pages_total':   ['pool_size',1],
                        'Innodb_data_fsyncs':               ['file_fsyncs',1],
                        'Innodb_data_pending_reads':        ['pending_normal_aio_reads',1],
                        'Innodb_data_pending_writes':       ['pending_normal_aio_writes',1],
                        'Innodb_os_log_pending_fsyncs':     ['pending_log_flushes',1],
                        'Innodb_pages_created':             ['pages_created',1],
                        'Innodb_pages_read':                ['pages_read',1],
                        'Innodb_pages_written':             ['pages_written',1],
                        'Innodb_rows_deleted':              ['rows_deleted',1],
                        'Innodb_rows_inserted':             ['rows_inserted',1],
                        'Innodb_rows_read':                 ['rows_read',1],
                        'Innodb_rows_updated':              ['rows_updated',1],
                        'Innodb_buffer_pool_reads':         ['pool_reads',1],
                        'Innodb_buffer_pool_read_requests': ['pool_read_requests',1],
                    }
                    for key in overrides.keys():
                        if status.has_key(key):
                            innodb_status[overrides[key][0]] = status[key]*overrides[key][1]
                    status.update(innodb_status)
            # Get response time histogram from Percona Server or MariaDB if enabled.
            if (status.has_key('have_response_time_distribution') and status[
                'have_response_time_distribution'] == 'YES') \
                    or ((status.has_key('query_response_time_stats') and status['query_response_time_stats'])):
                res = cls._run_query(
                    "SELECT `count`, ROUND(total * 1000000) AS total FROM INFORMATION_SCHEMA.QUERY_RESPONSE_TIME WHERE `time` <> 'TOO LONG'",
                    conn)
                if res and len(res) > 0:
                    rn = len(res)
                    for offset in range(0, 14):
                        item = res[offset] if offset < rn else [0, 0]
                        status["Query_time_count_%02d" % offset] = int(item[0])
                        status["Query_time_total_%02d" % offset] = int(item[1])
            else:
                # fill zero to query_time
                # TODO: use "select benchmark(10000, 1+1) " to calcute response time on no percona mysql
                for offset in range(0, 14):
                    status["Query_time_count_%02d" % offset] = 0
                    status["Query_time_total_%02d" % offset] = 0
            # Make table_open_cache backwards-compatible (issue 63).
            if status.has_key('table_open_cache'):
                status['table_cache'] = status['table_open_cache']
            # Compute how much of the key buffer is used and unflushed (issue 127).
            status['Key_buf_bytes_used'] = status['key_buffer_size'] - (
                status['Key_blocks_unused'] * status['key_cache_block_size'])
            status['Key_buf_bytes_unflushed'] = status['Key_blocks_not_flushed'] * status['key_cache_block_size']
            if status.has_key('unflushed_log') and status['unflushed_log']:
                # TODO: I'm not sure what the deal is here; need to debug this.  But the
                # unflushed log bytes spikes a lot sometimes and it's impossible for it to
                # be more than the log buffer.
                status['unflushed_log'] = max([status['unflushed_log'], status['innodb_log_buffer_size']])
            # Define the variables to output.  I use shortened variable names so maybe
            # it'll all fit in 1024 bytes for Cactid and Spine's benefit.  Strings must
            # have some non-hex characters (non a-f0-9) to avoid a Cacti bug.  This list
            # must come right after the word MAGIC_VARS_DEFINITIONS.  The Perl script
            # parses it and uses it as a Perl variable.
            exchange_keys = {
                'Key_read_requests': 'gg',
                'Key_reads': 'gh',
                'Key_write_requests': 'gi',
                'Key_writes': 'gj',
                'history_list': 'gk',
                'innodb_transactions': 'gl',
                'read_views': 'gm',
                'current_transactions': 'gn',
                'locked_transactions': 'go',
                'active_transactions': 'gp',
                'pool_size': 'gq',
                'free_pages': 'gr',
                'database_pages': 'gs',
                'modified_pages': 'gt',
                'pages_read': 'gu',
                'pages_created': 'gv',
                'pages_written': 'gw',
                'file_fsyncs': 'gx',
                'file_reads': 'gy',
                'file_writes': 'gz',
                'log_writes': 'hg',
                'pending_aio_log_ios': 'hh',
                'pending_aio_sync_ios': 'hi',
                'pending_buf_pool_flushes': 'hj',
                'pending_chkp_writes': 'hk',
                'pending_ibuf_aio_reads': 'hl',
                'pending_log_flushes': 'hm',
                'pending_log_writes': 'hn',
                'pending_normal_aio_reads': 'ho',
                'pending_normal_aio_writes': 'hp',
                'ibuf_inserts': 'hq',
                'ibuf_merged': 'hr',
                'ibuf_merges': 'hs',
                'spin_waits': 'ht',
                'spin_rounds': 'hu',
                'os_waits': 'hv',
                'rows_inserted': 'hw',
                'rows_updated': 'hx',
                'rows_deleted': 'hy',
                'rows_read': 'hz',
                'Table_locks_waited': 'ig',
                'Table_locks_immediate': 'ih',
                'Slow_queries': 'ii',
                'Open_files': 'ij',
                'Open_tables': 'ik',
                'Opened_tables': 'il',
                'innodb_open_files': 'im',
                'open_files_limit': 'in',
                'table_cache': 'io',
                'Aborted_clients': 'ip',
                'Aborted_connects': 'iq',
                'Max_used_connections': 'ir',
                'Slow_launch_threads': 'is',
                'Threads_cached': 'it',
                'Threads_connected': 'iu',
                'Threads_created': 'iv',
                'Threads_running': 'iw',
                'max_connections': 'ix',
                'thread_cache_size': 'iy',
                'Connections': 'iz',
                'slave_running': 'jg',
                'slave_stopped': 'jh',
                'Slave_retried_transactions': 'ji',
                'slave_lag': 'jj',
                'Slave_open_temp_tables': 'jk',
                'Qcache_free_blocks': 'jl',
                'Qcache_free_memory': 'jm',
                'Qcache_hits': 'jn',
                'Qcache_inserts': 'jo',
                'Qcache_lowmem_prunes': 'jp',
                'Qcache_not_cached': 'jq',
                'Qcache_queries_in_cache': 'jr',
                'Qcache_total_blocks': 'js',
                'query_cache_size': 'jt',
                'Questions': 'ju',
                'Com_update': 'jv',
                'Com_insert': 'jw',
                'Com_select': 'jx',
                'Com_delete': 'jy',
                'Com_replace': 'jz',
                'Com_load': 'kg',
                'Com_update_multi': 'kh',
                'Com_insert_select': 'ki',
                'Com_delete_multi': 'kj',
                'Com_replace_select': 'kk',
                'Select_full_join': 'kl',
                'Select_full_range_join': 'km',
                'Select_range': 'kn',
                'Select_range_check': 'ko',
                'Select_scan': 'kp',
                'Sort_merge_passes': 'kq',
                'Sort_range': 'kr',
                'Sort_rows': 'ks',
                'Sort_scan': 'kt',
                'Created_tmp_tables': 'ku',
                'Created_tmp_disk_tables': 'kv',
                'Created_tmp_files': 'kw',
                'Bytes_sent': 'kx',
                'Bytes_received': 'ky',
                'innodb_log_buffer_size': 'kz',
                'unflushed_log': 'lg',
                'log_bytes_flushed': 'lh',
                'log_bytes_written': 'li',
                'relay_log_space': 'lj',
                'binlog_cache_size': 'lk',
                'Binlog_cache_disk_use': 'll',
                'Binlog_cache_use': 'lm',
                'binary_log_space': 'ln',
                'innodb_locked_tables': 'lo',
                'innodb_lock_structs': 'lp',
                'State_closing_tables': 'lq',
                'State_copying_to_tmp_table': 'lr',
                'State_end': 'ls',
                'State_freeing_items': 'lt',
                'State_init': 'lu',
                'State_locked': 'lv',
                'State_login': 'lw',
                'State_preparing': 'lx',
                'State_reading_from_net': 'ly',
                'State_sending_data': 'lz',
                'State_sorting_result': 'mg',
                'State_statistics': 'mh',
                'State_updating': 'mi',
                'State_writing_to_net': 'mj',
                'State_none': 'mk',
                'State_other': 'ml',
                'Handler_commit': 'mm',
                'Handler_delete': 'mn',
                'Handler_discover': 'mo',
                'Handler_prepare': 'mp',
                'Handler_read_first': 'mq',
                'Handler_read_key': 'mr',
                'Handler_read_next': 'ms',
                'Handler_read_prev': 'mt',
                'Handler_read_rnd': 'mu',
                'Handler_read_rnd_next': 'mv',
                'Handler_rollback': 'mw',
                'Handler_savepoint': 'mx',
                'Handler_savepoint_rollback': 'my',
                'Handler_update': 'mz',
                'Handler_write': 'ng',
                'innodb_tables_in_use': 'nh',
                'innodb_lock_wait_secs': 'ni',
                'hash_index_cells_total': 'nj',
                'hash_index_cells_used': 'nk',
                'total_mem_alloc': 'nl',
                'additional_pool_alloc': 'nm',
                'uncheckpointed_bytes': 'nn',
                'ibuf_used_cells': 'no',
                'ibuf_free_cells': 'np',
                'ibuf_cell_count': 'nq',
                'adaptive_hash_memory': 'nr',
                'page_hash_memory': 'ns',
                'dictionary_cache_memory': 'nt',
                'file_system_memory': 'nu',
                'lock_system_memory': 'nv',
                'recovery_system_memory': 'nw',
                'thread_hash_memory': 'nx',
                'innodb_sem_waits': 'ny',
                'innodb_sem_wait_time_ms': 'nz',
                'Key_buf_bytes_unflushed': 'og',
                'Key_buf_bytes_used': 'oh',
                'key_buffer_size': 'oi',
                'Innodb_row_lock_time': 'oj',
                'Innodb_row_lock_waits': 'ok',
                'Query_time_count_00': 'ol',
                'Query_time_count_01': 'om',
                'Query_time_count_02': 'on',
                'Query_time_count_03': 'oo',
                'Query_time_count_04': 'op',
                'Query_time_count_05': 'oq',
                'Query_time_count_06': 'or',
                'Query_time_count_07': 'os',
                'Query_time_count_08': 'ot',
                'Query_time_count_09': 'ou',
                'Query_time_count_10': 'ov',
                'Query_time_count_11': 'ow',
                'Query_time_count_12': 'ox',
                'Query_time_count_13': 'oy',
                'Query_time_total_00': 'oz',
                'Query_time_total_01': 'pg',
                'Query_time_total_02': 'ph',
                'Query_time_total_03': 'pi',
                'Query_time_total_04': 'pj',
                'Query_time_total_05': 'pk',
                'Query_time_total_06': 'pl',
                'Query_time_total_07': 'pm',
                'Query_time_total_08': 'pn',
                'Query_time_total_09': 'po',
                'Query_time_total_10': 'pp',
                'Query_time_total_11': 'pq',
                'Query_time_total_12': 'pr',
                'Query_time_total_13': 'ps',
                'wsrep_replicated_bytes': 'pt',
                'wsrep_received_bytes': 'pu',
                'wsrep_replicated': 'pv',
                'wsrep_received': 'pw',
                'wsrep_local_cert_failures': 'px',
                'wsrep_local_bf_aborts': 'py',
                'wsrep_local_send_queue': 'pz',
                'wsrep_local_recv_queue': 'qg',
                'wsrep_cluster_size': 'qh',
                'wsrep_cert_deps_distance': 'qi',
                'wsrep_apply_window': 'qj',
                'wsrep_commit_window': 'qk',
                'wsrep_flow_control_paused': 'ql',
                'wsrep_flow_control_sent': 'qm',
                'wsrep_flow_control_recv': 'qn',
                'pool_reads': 'qo',
                'pool_read_requests': 'qp',
            }
            # for key in exchange_keys.keys():
            #     if not status.has_key(key): continue
            #     status[exchange_keys[key]]=status.pop(key)
            for key in status.keys():
                status[str(key).lower()] = status.pop(key)
        except Exception as e:
            traceback.print_exc()
            print e
        finally:
            if conn: conn.close()
            return status


if __name__ == "__main__":
    import json

    print json.dumps(
        MySQL_Monitor.get_monitor_data(host=sys.argv[1], port=int(sys.argv[2]), user=sys.argv[3], passwd=sys.argv[4]),
        indent=4,
        sort_keys=True)