service monitor scripts for zabbix
=============================
This project is used for get some services status data in zabbix agent


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
##Zabbix LLD
    zbxmon --discovery --macros MYSQLIP/MYSQLPORT --service mysql --extend zabbixmonitor/zabbixmonitor
The 'zabbixmonitor' is user/password of mysql, if it can not access mysql, we will try use the sock file to accessing 
mysql, and add this user    
output:
    
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
##Get status data   
    zbxmon --service mysql --item additional_pool_alloc --instance 192.168.1.1/3306 --extend zabbixmonitor/zabbixmonitor
   
#In zabbix agent conf
Add this lines:
    
    UserParameter=service.status[*],/path/to/zbxmon --service=$1 --item=$2 --instance=$3 --extend=$4
    UserParameter=service.discovery[*],/path/to/zbxmon --service=$1 --discovery --macros=$2 --extend=$3
