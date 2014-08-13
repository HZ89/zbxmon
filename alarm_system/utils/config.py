# -*- coding: utf-8 -*-
__author__ = 'Harrison'
import ConfigParser
import os
import sys
import getopt
from alarm_system.exceptions import AlarmConfigError
from alarm_system.utils.error import raise_error

DEFAULT_SETTING = {
    'rabbitmq': {
        'ip': '127.0.0.1',
        'port': '',
        'vhost': '/',
        'user': ''
    },
    'http_api': {
        'port': '8888',
        'listen_ip': '127.0.0.1',
    },
}
ALL_SECTIONS = ['rabbitmq', 'http_api']
MINI_SECTIONS = ['rabbitmq', 'http_api']
CLI_OPTS_DEST = {
    'd,daemon': 'run server as a daemon',
    'h,help': 'print this message',
    'c:,config-file=': 'config file path (e.g: --config-file=/tmp/alarm.ini)',
    'v,version': 'print version',
    'l:,log-level=': 'defind log level, must in "wanning","errors","debug"',
}

def _usage():
    print "{0} [OPTION]".format(sys.argv[0])
    print "optional arguments:"
    for opt in CLI_OPTS_DEST.keys():
        print "-{0}, --{1}:\t\t{2}".format(opt.split(',')[0][1:], opt.split(',')[1], CLI_OPTS_DEST[opt])



def cli_opt_parse():
    cli_opts= {}
    shot_opt = ''.join([ x.split(',')[0] for x in CLI_OPTS_DEST.keys()])
    long_opt = [ x.split(',')[1] for x in CLI_OPTS_DEST.keys() ]
    try:
        opts, args = getopt.getopt(sys.argv[1:], shot_opt, long_opt)
    except getopt.GetoptError as err:
        print str(err)
        _usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--version"):
            cli_opts['version'] = True
        elif o in ("-h", "--help"):
            cli_opts['help'] = True
        elif o in ("-c", "--config-file"):
            cli_opts['config_path'] = a
        elif o in ("-d", "--daemon"):
            cli_opts['daemon'] = True
        elif o in ("-l", "--log-level"):
            cli_opts['log_level'] = a
        else:
            raise_error(AlarmConfigError, msg='{0} is a unhandled option'.format(a))
    return cli_opts
        

class ConfigMeta(type):
    def __init__(cls, name, bases, dict):
        super(ConfigMeta, cls).__init__(name, bases, dict)
        cls.instance = None
    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(ConfigMeta, cls).__call__(*args, **kwargs)
            return cls.instance

class Config(object):
    __metaclass__ = ConfigMeta
#default path just make sure the app can startup
    def __init__(self, config_file='/tmp/alarm_system.ini'):
        self.configobj = ConfigParser.ConfigParser(allow_no_value=True)
        if os.path.isfile(config_file):
            self.configobj.readfp(open(config_file))
            self.verify_config_file()
        else:
            self.parser_sections()
            with open(config_file, 'wb') as config_file_fd:
                self.configobj.write(config_file_fd)
            config_file_fd.close()

    def parser_sections(self, defautl_seting=DEFAULT_SETTING):
        for key in defautl_seting.keys():
            if isinstance(defautl_seting[key], dict):
                self.configobj.add_section(key)
                for options in defautl_seting[key].keys():
                    self.configobj.set(key, options, defautl_seting[key][options])
            else:
                raise #log the value in logfile with error

    def verify_config_file(self):
        sections_from_file = self.configobj.sections()
        for section in MINI_SECTIONS:
            if not section in sections_from_file:
                raise_error(AlarmConfigError, msg= 'can not fined %s section' % section)
        for section in sections_from_file:
            if not section in ALL_SECTIONS:
                raise_error(AlarmConfigError, msg= '%s is invalid' % section)

    def get_section(self, section):
        items = self.configobj.items(section)
        return {x: y for x, y in items}
