zabbix_service_monitor_script
=============================
本脚本的主要功能呢个是实现mysql，redis，memcached，mongodb多实例监控，自动发现（用于zabbix LLD）
在脚本执行过程中，每个监控时刻对每个实例的监控链接只有一个，减少由于监控行为带来的观察误差
