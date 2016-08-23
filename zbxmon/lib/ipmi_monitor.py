#!/app/bin/python2.7
# -*- coding: utf8 -*-

import re
import os
import time
import commands
from zbxmon.monitor import Monitor


# class MyException(Exception):pass
# try:
#     if not os.path.exists('/usr/bin/ipmitool'):
#         raise MyException
# except MyException:
#     print "ipmitool command not found"
#     exit()


def discovery_ipmi(arg='', *args):
    '''
    discovery ipmi instance
    '''
    result = []
    host = Monitor.get_local_ip()
    if not arg:
        result.append([host])
    elif arg == 'FAN':
        (status, output) = commands.getstatusoutput(
            "/usr/bin/ipmitool sdr type fan | grep -v 'Fully Redundant' | cut -d '|' -f 1 ")
        if status == 0:
            for fan in output.split('\n'):
                fan = fan.lower()
                fan = fan.strip()
                fan = fan.replace(' ', '_')
                result.append([host, fan])
    # cpu memory system io
    elif arg == 'CMSI':
        (status, output) = commands.getstatusoutput(
            "/usr/bin/ipmitool sdr elist full | grep -E '(CPU|IO|MEM|SYS)'| cut -d '|' -f 1")
        if status == 0:
            for cmsi in output.split('\n'):
                cmsi = cmsi.lower()
                cmsi = cmsi.strip()
                cmsi = cmsi.replace(' ', '_')
                result.append([host, cmsi])
    # current voltage temp
    elif arg == 'VCT':
        (status, output) = commands.getstatusoutput(
            "/usr/bin/ipmitool sdr elist full | grep -E '(Inlet Temp|Exhaust Temp|Current|Voltage)'| cut -d '|' -f 1")
        if status == 0:
            for vct in output.split('\n'):
                vct = vct.lower()
                vct = vct.strip()
                vct = vct.replace(' ', '_')
                result.append([host, vct])
    elif arg == 'PW':
        (status, output) = commands.getstatusoutput(
            "/usr/bin/ipmitool chassis status | grep -E '(System Power|Power Overload)' | cut -d ':' -f 1")
        if status == 0:
            for pw in output.split('\n'):
                pw = pw.lower()
                pw = pw.strip()
                pw = pw.replace(' ', '_')
                result.append([host, pw])
    elif arg == 'SEL':
        (status, output) = commands.getstatusoutput(
            "/usr/bin/ipmitool sel info | grep -v Information | cut -d ':' -f 1")
        if status == 0:
            for sel in output.split('\n'):
                sel = sel.lower()
                sel = sel.strip()
                sel = sel.replace(' ', '_')
                result.append([host, sel])

    return result


def get_ipmi_data(instance_name='', arg=''):
    #    print instance_name
    result = {}

    if arg == 'FAN':
        (status, output) = commands.getstatusoutput("/usr/bin/ipmitool sdr type fan | grep -v 'Fully Redundant'")
        if status == 0:
            for fan in output.split('\n'):
                l_fan = fan.split('|')
                k = l_fan[0].strip().lower().replace(' ', '_')
                v = l_fan[2].strip() + '|' + l_fan[4].strip()
                result[k] = v
                # print result

    if arg == 'CMSI':
        (status, output) = commands.getstatusoutput("/usr/bin/ipmitool sdr elist full | grep -E '(CPU|IO|MEM|SYS)'")
        if status == 0:
            for cmsi in output.split('\n'):
                l_cmsi = cmsi.split('|')
                k = l_cmsi[0].strip().lower().replace(' ', '_')
                v = l_cmsi[2].strip() + '|' + l_cmsi[4].strip()
                result[k] = v

    if arg == 'VCT':
        (status, output) = commands.getstatusoutput(
            "/usr/bin/ipmitool sdr elist full | grep -E '(Inlet Temp|Exhaust Temp|Current|Voltage)'")
        if status == 0:
            for vct in output.split('\n'):
                l_vct = vct.split('|')
                k = l_vct[0].strip().lower().replace(' ', '_')
                v = l_vct[2].strip() + '|' + l_vct[4].strip()
                result[k] = v

    if arg == 'PW':
        (status, output) = commands.getstatusoutput(
            "/usr/bin/ipmitool chassis status | grep -E '(System Power|Power Overload)'")
        if status == 0:
            for pw in output.split('\n'):
                l_pw = pw.split(':')
                k = l_pw[0].strip().lower().replace(' ', '_')
                v = l_pw[1].strip()
                result[k] = v

    if arg == 'SEL':
        (status, output) = commands.getstatusoutput("/usr/bin/ipmitool sel info | grep -v Information")
        if status == 0:
            for sel in output.split('\n'):
                l_sel = sel.split(':')
                k = l_sel[0].strip().lower().replace(' ', '_')
                v = l_sel[1].strip()
                result[k] = v

    if arg == 'LOG':
        # 48 hours
        limit = 172800
        log_content = ''
        (status, output) = commands.getstatusoutput("/usr/bin/ipmitool sel list")
        if status == 0:
            for log in output.split('\n'):
                #                print log
                t_id = log.split('|')[0].strip()
                t_date = log.split('|')[1].strip()
                if t_date == 'Pre-Init':
                    continue
                t_time = log.split('|')[2].strip()
                t_sensor = log.split('|')[3].strip()
                t_desc = log.split('|')[4].strip()
                t_event_direction = log.split('|')[5].strip()
                log_time_str = t_date + '|' + t_time
                log_time = time.mktime(time.strptime(log_time_str, '%m/%d/%Y|%H:%M:%S'))
                cur_time = time.time()
                time_diff = cur_time - log_time
                # 3 | 10/20/2014 | 11:28:21 | Physical Security #0x73 | General Chassis intrusion () | Deasserted
                if time_diff < limit:
                    log_content += """SEL_Record_ID='{0}'  Log_Time='{1}'  Sensor='{2}'  Description='{3}'  Event_Direction='{4}'\n\n""".format(
                        t_id, t_date + ' ' + t_time, t_sensor, t_desc, t_event_direction)
                else:
                    continue

            if not log_content:
                log_content = 'None'
            result['log'] = log_content
        #                print log_time

    return result


if __name__ == "__main__":
    get_ipmi_data()
