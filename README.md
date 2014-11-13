zabbix_service_monitor_script
=============================
本脚本的主要功能是实现mysql，redis，memcached，mongodb多实例监控，自动发现（用于zabbix LLD）  
在脚本执行过程中，每个监控时刻对每个实例的监控链接只有一个，减少由于监控行为带来的观察误差


#optional arguments:
*  -h, --help            show this help message and exit
*  --discovery, -D       Discovery the service instance and return json data
*  --service SERVICE, -S SERVICE the service name of monitor
*  --instance INSTANCE, -I INSTANCE the name of the instance you want
*  --item ITEM, -K ITEM  the item of you want
*  --macros MACROS, -M MACROS the macro list, used to build discovery data eg:p1/p2/p3
*  --extend EXTEND, -E EXTEND extend args eg. p/p1/p2
*  --cache CACHE, -C CACHE cache path
*  --list, -L            list monitor items for this instance

  
#example:
##discovery
    zsmc --discovery --macros MYSQLIP/MYSQLPORT --service mysql --extend zabbixmonitor/zabbixmonitor
zabbixmonitor为监控用账户密码，若此用户链接失败会尝试寻找sock文件进行连接  
输出如下:
    
    {
      "data": [
        {
          "{#MYSQLIP}": "192.168.1.1",
          "{#MYSQLPORT}": "3306"
        },
        {
          "{#MYSQLIP}": "192.168.1.1",
          "{#MYSQLPORT}": "3307"
        },
        {
          "{#MYSQLIP}": "192.168.1.1",
          "{#MYSQLPORT}": "3308"
        }
      ]
    }
##获取数据    
    zsmc --service mysql --item additional_pool_alloc --instance 192.168.1.1/3306 --extend zabbixmonitor/zabbixmonitor
   
#zabbix agent 配置
在zabbix agentd配置中添加:
    
    UserParameter=service.status[*],/path/to/zsmc --service=$1 --item=$2 --instance=$3 --extend=$4
    UserParameter=service.discovery[*],/path/to/zsmc --service=$1 --discovery --macros=$2 --extend=$3
