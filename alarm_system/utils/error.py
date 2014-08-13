# -*- coding: utf-8 -*-
__author__ = 'Harrison'

import exceptions
import alarm_system.exceptions

def raise_error(name=None, args=None, msg=''):
    name = name or Exception
    if hasattr(alarm_system.exceptions, name.__name__):
        ex = getattr(alarm_system.exceptions, name.__name__)
    elif hasattr(exceptions, name.__name__):
        ex = getattr(exceptions, name.__name__)
    else:
        name = alarm_system.exceptions.AlarmException
        ex = getattr(alarm_system.exceptions, name.__name__)
    if args is not None:
        raise ex(*args)
    else:
        raise ex(msg)