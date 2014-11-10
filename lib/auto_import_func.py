# -*- coding: utf8 -*-

from importlib import import_module


def get_func_list(service):
    p = '{}_monitor'.format(service)
    mod = import_module(p)
    try:
        discovery_func = getattr(mod, 'discovery_{}'.format(service))
    except AttributeError:
        discovery_func = None

    get_data_func = getattr(mod, 'get_{}_data'.format(service))

    return get_data_func, discovery_func
