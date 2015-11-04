#!/opt/17173_install/python-2.7.6/bin/python2.7
#-*- coding: utf8 -*-

__author__ = 'Harrison'
from zbxmon.monitor import Monitor
from argh import ArghParser, arg, expects_obj
import argparse

# TODO:Completion script comments

# UserParameter=service.status[*],/opt/17173_install/zabbix-2.4.1/externalscripts/monitor --service=$1 --item=$2 --instance=$3 --extend=$4
# UserParameter=service.discovery[*],/opt/17173_install/zabbix-2.4.1/externalscripts/monitor  --service=$1 --discovery --macros=$2 --extend=$3

@arg('--discovery', '-D', default=False, required=False, help='Discovery the service instance and return json data')
@arg('--service', '-S', required=True, help='the service name of monitor')
@arg('--instance', '-I', help='the name of the instance you want')
@arg('--item', '-K', help='the item of you want')
@arg('--macros', '-M', help='the macro list, used to build discovery data eg:p1,p2,p3')
@arg('--extend', '-E', help='extend args eg. p,p1,p2')
@arg('--cache', '-C', help='cache path')
@arg('--list', '-L', default=False, help='list monitor items for this instance')
@expects_obj
def start(args):
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

    monitor = Monitor(args.service, cache_path=args.cache if args.cache else None)

    if args.discovery:
        print monitor.discovery(args.macros.split('/'), *arg_list)
    else:
        if args.item:
            print monitor.load_data(args.instance, args.item, *arg_list)
        if args.list:
            print "Monitor Items (in %s)" % args.instance
            for it in sorted(monitor.load_keys(args.instance, *arg_list)):
                print it


def zsmc_main():
    parser = ArghParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.set_default_command(start)
    parser.dispatch()

if __name__ == '__main__':
    zsmc_main()