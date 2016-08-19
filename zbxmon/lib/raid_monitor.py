#!/app/bin/python2.7
# -*- coding: utf8 -*-

import re
import commands
from zbxmon.monitor import Monitor

def discovery_raid(*args):
    '''
    discovery raid instance's adapters and disks
    '''
    ( status, output ) = commands.getstatusoutput('which MegaCli')
    if status:
        print 'No such file: MegaCli'
        exit()
        
    adp_list = []
    enc_list = []
    virt_list = []
    dev_list = []
    result = []

    sys_cmd = "MegaCli -adpCount | grep Controller | awk '{print $3}' | awk -F '.' '{print $1}'"
    (status, output) = commands.getstatusoutput(sys_cmd)
    if not status:
        adp_num = output.strip()
        for i in range(int(adp_num)):
            adp_list.append(i)

    for adp_id in adp_list:
        # enclosures id
        sys_cmd = "MegaCli -EncInfo -a{} | grep 'Device ID' | cut -d ':' -f 2".format(adp_id)
        (status, output) = commands.getstatusoutput(sys_cmd)
        if not status:
            enc_id = output.strip()
            enc_list.append(enc_id)

    for adp_id in adp_list:
        # virtual disk id
        sys_cmd = "MegaCli -LDGetNum -a{} | grep 'Number' | cut -d ':' -f 2".format(adp_id)
        (status, output) = commands.getstatusoutput(sys_cmd)
        if not status:
            virt_num = output.strip()
            for i in range(int(virt_num)):
                virt_list.append(i)

    for adp_id in adp_list:
       	# disk id
        sys_cmd = "MegaCli -PDGetNum -a{0} | grep 'Number' | cut -d ':' -f 2".format(adp_id)
        (status, output) = commands.getstatusoutput(sys_cmd)
        if not status:
            dev_num = output.strip()
            for i in range(int(dev_num)):
                dev_list.append(i) 

    # return result list
    if args and args.strip() == 'BBU':
        for adp in adp_list:
            result.append([adp])
    elif args and args.strip() == 'LD':
        for adp in adp_list:
            for virt in virt_list:
                result.append([adp, virt])
    elif args and args.strip() == 'PD':
        for adp in adp_list:
            for enc in enc_list:
                for dev in dev_list:
                    result.append([adp, dev, enc])
        
    return result



def get_raid_data(instance_name='', *args):

    result = {}

    if args and list(args)[0] == 'BBU':

        adapter = instance_name.strip()
#	print adapter

        extend = list(args)[0]
        sys_cmd = "MegaCli -AdpBbuCmd -GetBbuStatus -a{0}".format(adapter)
        
        (status, output) = commands.getstatusoutput(sys_cmd)
        if not status:
            p = re.compile('\s+Voltage\s+:\s+\w+', re.I)
            m = p.search(output)
            if m:
                result['voltage'] = m.group(0).split(':')[1].strip()

            p = re.compile('Temperature\s+:\s+\w+', re.I)
            m = p.search(output)
            if m:
                result['temperature'] = m.group(0).split(':')[1].strip()
        
            p = re.compile('Learn Cycle Status.*', re.I)
            m = p.search(output)
            if m:
                result['LCS'] = m.group(0).split(':')[1].strip()
        
            p = re.compile('Remaining Capacity:.*', re.I)
            m = p.search(output)
            if m:
                result['RC'] = m.group(0).split()[2].strip()
        
            p = re.compile('Full Charge Capacity.*', re.I)
            m = p.search(output)
            if m:
                result['FCC'] = m.group(0).split(':')[1].strip()
        
    elif args and list(args)[0] == 'LD':
    	
        adapter = instance_name.split('/')[0].strip()
    	virtual = instance_name.split('/')[1].strip()
        sys_cmd = "MegaCli -LDInfo -L{0} -a{1}".format(virtual, adapter)
        (status, output) = commands.getstatusoutput(sys_cmd)
        if not status:
            p = re.compile('RAID Level.*', re.I)
            m = p.search(output)
            if m:
                result['raid_level'] = m.group(0).split(':')[1].strip()
                if result['raid_level'] == 'Primary-1, Secondary-0, RAID Level Qualifier-0':
                    result['raid_level'] = 'raid 1'
                elif result['raid_level'] == 'Primary-0, Secondary-0, RAID Level Qualifier-0':
                    result['raid_level'] = 'raid 0'
                elif result['raid_level'] == 'Primary-5, Secondary-0, RAID Level Qualifier-3':
                    result['raid_level'] = 'raid 5'
                elif result['raid_level'] == 'Primary-1, Secondary-3, RAID Level Qualifier-0':
                    result['raid_level'] = 'raid 3'

            p = re.compile('Size.*', re.I)
            m = p.search(output)
            if m:
                result['size'] = m.group(0).split(':')[1].strip()

            p = re.compile('State.*', re.I)
            m = p.search(output)
            if m:
                result['state'] = m.group(0).split(':')[1].strip()

            p = re.compile('Strip Size.*', re.I)
            m = p.search(output)
            if m:
                result['strip_size'] = m.group(0).split(':')[1].strip()

            p = re.compile('Number Of Drives.*', re.I)
            m = p.search(output)
            if m:
                result['drive_number'] = m.group(0).split(':')[1].strip()

            p = re.compile('Default Cache Policy.*', re.I)
            m = p.search(output)
            if m:
                result['default_cache_policy'] = m.group(0).split(':')[1].strip()

            p = re.compile('Current Cache Policy.*', re.I)
            m = p.search(output)
            if m:
                result['current_cache_policy'] = m.group(0).split(':')[1].strip()

            p = re.compile('Access Policy.*', re.I)
            m = p.search(output)
            if m:
                result['access_policy'] = m.group(0).split(':')[1].strip()

            p = re.compile('Disk Cache Policy.*', re.I)
            m = p.search(output)
            if m:
                result['disk_cache_policy'] = m.group(0).split(':')[1].strip()

            p = re.compile('Bad Blocks Exist.*', re.I)
            m = p.search(output)
            if m:
                result['bad_blocks_exists'] = m.group(0).split(':')[1].strip()

    elif args and list(args)[0] == 'PD':

        adapter = instance_name.split('/')[0].strip()
        disk = instance_name.split('/')[1].strip()
        enclosure = instance_name.split('/')[2].strip()

        sys_cmd = "MegaCli -pdInfo -PhysDrv[{2}:{1}] -a{0}".format(adapter, disk, enclosure)

        (status, output) = commands.getstatusoutput(sys_cmd)
        if not status:

            p = re.compile('Enclosure Device ID.*', re.I)
            m = p.search(output)
            if m:
                result['enclosure_id'] = m.group(0).split(':')[1].strip()

            p = re.compile('Slot Number.*', re.I)
            m = p.search(output)
            if m:
                result['slot_number'] = m.group(0).split(':')[1].strip()
    
            p = re.compile('Device Id.*', re.I)
            m = p.search(output)
            if m:
                result['device_id'] = m.group(0).split(':')[1].strip()

            p = re.compile('Media Error Count.*', re.I)
            m = p.search(output)
            if m:
                result['MEC'] = m.group(0).split(':')[1].strip()
    
            p = re.compile('Other Error Count.*', re.I)
            m = p.search(output)
            if m:
                result['OEC'] = m.group(0).split(':')[1].strip()
    
            p = re.compile('Predictive Failure Count.*', re.I)
            m = p.search(output)
            if m:
                result['PFC'] = m.group(0).split(':')[1].strip()

            p = re.compile('PD Type.*', re.I)
            m = p.search(output)
            if m:
                result['PD_type'] = m.group(0).split(':')[1].strip()

            p = re.compile('Raw Size.*', re.I)
            m = p.search(output)
            if m:
                result['raw_size'] = m.group(0).split()[2].strip()+m.group(0).split()[3].strip()

            p = re.compile('Firmware state.*', re.I)
            m = p.search(output)
            if m:
                result['firmware_state'] = m.group(0).split(':')[1].strip()
    
            p = re.compile('Inquiry Data.*', re.I)
            m = p.search(output)
            if m:
                result['inquiry_data'] = m.group(0).split(':')[1].strip()

            p = re.compile('Device Speed.*', re.I)
            m = p.search(output)
            if m:
                result['device_speed'] = m.group(0).split(':')[1].strip()

            p = re.compile('Link Speed.*', re.I)
            m = p.search(output)
            if m:
                result['link_speed'] = m.group(0).split(':')[1].strip()

            p = re.compile('Drive Temperature.*', re.I)
            m = p.search(output)
            if m:
                result['drive_temperature'] = m.group(0).split()[2].lstrip(':').rstrip('C')

#    print result
    return result


if __name__ == "__main__":
    get_raid_data()
