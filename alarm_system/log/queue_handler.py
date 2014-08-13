# -*- coding: utf-8 -*-
__author__ = 'Harrison'
import logging
import logging.handlers
import datetime
from multiprocessing import Queue

try:
    from pytz import utc as _UTC
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False

class NewStyleClass(object):
    '''
    Simple new style class to make pylint shut up!
    '''

class QueueHandler(logging.Handler, NewStyleClass):
    def __init__(self, input_queue, level=logging.NOTSET):
        super(QueueHandler, self).__init__(level)
        assert issubclass(input_queue, Queue)
        self.queue = input_queue

    def emit(self, record):
        formatted_obj = self.format(record)
        self.queue.put(formatted_obj)

class LogAlarmFormatter(logging.Formatter, NewStyleClass):
    def __init__(self, msg_type='logalarm', msg_path='logalarm'):
        self.msg_type = msg_type
        self.msg_path = msg_path
        super(LogAlarmFormatter, self).__init__(fmt=None, datefmt=None)

    def formatTime(self, record, datefmt=None):
        timestamp = datetime.datetime.utcfromtimestamp(record.created)
        if HAS_PYTZ:
            return _UTC.localuze(timestamp).isoformat()
        return '{0}+00:00'.format(timestamp.isoformat())

    def format(self, record):
