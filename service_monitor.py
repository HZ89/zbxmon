#!/opt/17173_install/python-2.7.6/bin/python2.7
# -*- coding: utf8 -*-

__author__ = 'Harrison'

import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib'))
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from lib.monitor import Monitor
from functools import partial
from argh import ArghParser, arg
import argparse
from lib.auto_import_func import get_func_list

# TODO:Completion script comments

# UserParameter=service.status[*],/opt/17173_install/zabbix-2.4.1/externalscripts/service_monitor.py --service=$1 --item=$2 --instance=$3 --extend=$4
# UserParameter=service.discovery[*],/opt/17173_install/zabbix-2.4.1/externalscripts/service_monitor.py  --service=$1 --discovery --macros=$2 --extend=$3

class ServiceMonitor(Monitor):
    def __init__(self, service, instance=None, cache_path=None):
        self.service = service
        app = self.service + '_' + instance if instance else 'default'
        self.get_data_func, self.discovery_func = get_func_list(self.service)
        super(ServiceMonitor, self).__init__(app, cache_path)

    @classmethod
    def _get_bin_name(cls, service):
        BIN = {
            'mysql': 'mysqld',
            'redis': 'redis-server',
            'memcache': 'memcached',
            'mongodb': 'mongod',
        }
        return BIN[service]

    def load_data(self, instance, item=None, *args):
        """
        auto load func to get monitor data
        @param service: the name of service
        @param instance: string of the instance like ip:port or /dev/sda etc.
        @param is_discovery: is a zabbix low level discovery action
        @param args: other args like the args of func get_XXX_data
        @return: string
        """

        get_func = partial(self.get_data_func, instance)

        # add args
        if args:
            get_func = partial(get_func, *args)
        return self.get_item(instance=instance, item=item, get_monitor_data_func=get_func)

    def load_keys(self, instance, *args):
        """
        auto load func to get monitor data
        @param service: the name of service
        @param instance: string of the instance like ip:port or /dev/sda etc.
        @param is_discovery: is a zabbix low level discovery action
        @param args: other args like the args of func get_XXX_data
        @return: string
        """

        get_func = partial(self.get_data_func, instance)
        # add args
        if args:
            get_func = partial(get_func, *args)

        keys = self.get_keys(instance=instance, get_monitor_data_func=get_func)
        return keys

    def discovery(self, macro_name_list, *args):

        if self.discovery_func:
            discovery_func = self.discovery_func
            if args:
                discovery_func = partial(discovery_func, *args)
        else:
            discovery_func = partial(ServiceMonitor.get_ip_port, ServiceMonitor._get_bin_name(self.service))
        return ServiceMonitor.get_discovery_data(macro_name_list, discovery_func)


    # @classmethod
    # def discovery_phpfpm(cls, *args):
    # """
    # find local php-fpm process from config files
    # @param args: first value is config dir root, second value is regular used for find php-fpm config file
    # @return:
    #     """
    #     import ConfigParser
    #     config_path = args[0]
    #     prog = re.compile(args[1])
    #     fpm_conf = []
    #     if os.path.isdir(config_path):
    #         for root_dir, dirs, files in os.walk(config_path):
    #             for file in files:
    #                 if prog.match(file):
    #                     config = ConfigParser.RawConfigParser()
    #                     config.read(file)
    #                     for section in config.sections():
    #                         if section == 'global':
    #                             continue
    #                         pool = {}
    #                         for item, value in config.items(section):

@arg('--discovery', '-D', default=False, required=False, help='Discovery the service instance and return json data')
@arg('--service', '-S', required=True, help='the service name of monitor')
@arg('--instance', '-I', help='the name of the instance you want')
@arg('--item', '-K', help='the item of you want')
@arg('--macros', '-M', help='the macro list, used to build discovery data eg:p1,p2,p3')
@arg('--extend', '-E', help='extend args eg. p,p1,p2')
@arg('--cache', '-C', help='cache path')
@arg('--list', '-L', default=False, help='list monitor items for this instance')
def main(args):
    """
    get service monitor data, or discovery service instance
    @param args:
    @return: string when get service data, json when discovery
    """
    if args.discovery:
        assert not args.macros is None, 'must have macros'
    else:
        assert not args.instance is None, 'must have instance'
        # assert not args.item is None, 'must have item'

    arg_list = []
    if args.extend:
        arg_list = args.extend.split('/')

    if args.discovery:
        print ServiceMonitor.discovery(args.service, args.macros.split('/'), *arg_list)
    else:
        monitor = ServiceMonitor(args.service, cache_path=args.cache if args.cache else None)
        if args.item:
            print monitor.load_data(args.service, args.instance, args.item, *arg_list)
        if args.list:
            print "Monitor Items (in %s)" % args.instance
            for it in sorted(monitor.load_keys(args.service, args.instance, *arg_list)):
                print it


if __name__ == '__main__':
    parser = ArghParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.set_default_command(main)
    parser.dispatch()
