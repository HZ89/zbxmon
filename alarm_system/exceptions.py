# -*- coding: utf-8 -*-
__author__ = 'Harrison'
import copy
import alarm_system.utils

class AlarmException(Exception):
    '''
    Base exception class
    '''

class AlarmConfigError(AlarmException):
    '''
    Problem reading the config file
    '''

class AlarmSystemExit(SystemExit):
    '''
    This exception is raised when an unknown problem is found. Nothing else to do, just exit
    '''
    def __init__(self, code=0, msg=None):
        SystemExit.__init__(self, code)
        if msg:
            self.message = msg