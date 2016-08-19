#!/app/bin/python2.7
# -*- coding: utf8 -*-
__author__ = 'gaobiling'
__verion__ = '0.5.0'
import os
import string
import re
import psutil
from zbxmon.monitor import Monitor
import flup_fcgi_client as fcgi_client
import xml.etree.ElementTree as ET
import commands

BINNAME = 'java'

def discovery_tomcat():
    '''
    discovery tomcat instance's host and port
    '''
    result = []
    port = ''
    cmdline = []
    host = Monitor.get_local_ip()
    for i in psutil.process_iter():
        if i.name() == BINNAME:
            pid = int(i.pid)
            cmdline = i.cmdline()

            for opt in cmdline:
                if opt.find('-Dcom.sun.management.jmxremote.port') == 0:
                    monitor_port = opt.strip().split('=')[1]
                if opt.find('-Dcatalina.base') == 0:
                    config_file = opt.strip().split('=')[1] + '/conf/server.xml'
                    tree = ET.ElementTree(file=config_file)
                    root = tree.getroot()
                    for root_child in root:
                        if root_child.tag == 'Service':
                            for service_child in root_child:
                                if service_child.tag == 'Connector':
                                    listen_port = service_child.attrib['port']

            if monitor_port.isdigit() and listen_port.isdigit():
                result.append([host,listen_port,monitor_port])
    return result


def get_tomcat_data(instance_name=''):
    '''
    get tomcat monitor data by jmxcmd.jar
    '''
    ip = instance_name.split('/')[0]
    listen_port = instance_name.split('/')[1]
    monitor_port = instance_name.split('/')[2]
    jmx = '/app/bin/jmxcmd.jar'
    result = {}
    if not os.path.exists(jmx):
        return 'Not Found /app/bin/jmxcmd.jar'
    
    # java.lang:type=Memory HeapMemoryUsage
    sys_cmd = "java -jar %s - %s:%s java.lang:type=Memory NonHeapMemoryUsage" % (jmx,ip,monitor_port)
    (status, output) = commands.getstatusoutput(sys_cmd)
    if not status:
        for i in output.split('\n'):
            if i.find('committed:') == 0:
                m_committed = i.split(' ')[-1].strip()
                result['mem_committed'] = m_committed
            elif i.find('init:') == 0:
                m_init = i.split(' ')[-1].strip()
                result['mem_init'] = m_init
            elif i.find('max:') == 0:
                m_max = i.split(' ')[-1].strip()
                result['mem_max'] = m_max
            elif i.find('used:') == 0:
                m_used = i.split(' ')[-1].strip()
                result['mem_used'] = m_used

    # java.lang:type=ClassLoading LoadedClassCount
    sys_cmd = "java -jar %s - %s:%s java.lang:type=ClassLoading LoadedClassCount" % (jmx,ip,monitor_port)
    (status, output) = commands.getstatusoutput(sys_cmd)
    if not status:
        load_class_count = output.split(' ')[-1].strip()
        result['load_class_count'] = load_class_count

    # java.lang:type=ClassLoading TotalLoadedClassCount
    sys_cmd = "java -jar %s - %s:%s java.lang:type=ClassLoading TotalLoadedClassCount" % (jmx,ip,monitor_port)
    (status, output) = commands.getstatusoutput(sys_cmd)
    if not status:
        total_load_class_count = output.split(' ')[-1].strip()
        result['total_load_class_count'] = total_load_class_count

    # java.lang:type=ClassLoading UnloadedClassCount
    sys_cmd = "java -jar %s - %s:%s java.lang:type=ClassLoading UnloadedClassCount" % (jmx,ip,monitor_port)
    (status, output) = commands.getstatusoutput(sys_cmd)
    if not status:
        unload_class_count = output.split(' ')[-1].strip()
        result['unload_class_count'] = unload_class_count

    # java.lang:type=Threading PeakThreadCount
    sys_cmd = "java -jar %s - %s:%s java.lang:type=Threading PeakThreadCount" % (jmx,ip,monitor_port)
    (status, output) = commands.getstatusoutput(sys_cmd)
    if not status:
        peak_thread_count = output.split(' ')[-1].strip()
        result['peak_thread_count'] = peak_thread_count

    # java.lang:type=Threading ThreadCount
    sys_cmd = "java -jar %s - %s:%s java.lang:type=Threading ThreadCount" % (jmx,ip,monitor_port)
    (status, output) = commands.getstatusoutput(sys_cmd)
    if not status:
        thread_count = output.split(' ')[-1].strip()
        result['thread_count'] = thread_count
                
    # java.lang:type=Threading TotalStartedThreadCount
    sys_cmd = "java -jar %s - %s:%s java.lang:type=Threading TotalStartedThreadCount" % (jmx,ip,monitor_port)
    (status, output) = commands.getstatusoutput(sys_cmd)
    if not status:
        total_start_thread_count = output.split(' ')[-1].strip()
        result['total_start_thread_count'] = total_start_thread_count
                
    # Catalina:type=Server serverInfo
    sys_cmd = "java -jar %s - %s:%s Catalina:type=Server serverInfo" % (jmx,ip,monitor_port)
    (status, output) = commands.getstatusoutput(sys_cmd)
    if not status:
        server_info = output.split(' ')[-1].strip()
        result['server_info'] = server_info
                
    return result

if __name__ == "__main__":
    get_tomcat_data()
