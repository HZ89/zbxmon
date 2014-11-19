# -*- coding: utf8 -*-

from importlib import import_module


def get_func_list(service):
    prefix =  ".".join(__name__.split('.')[:-1])
    p = '{}.{}_monitor'.format(prefix, service)
    mod = import_module(p)
    try:
        discovery_func = getattr(mod, 'discovery_{}'.format(service))
    except AttributeError:
        discovery_func = None

    get_data_func = getattr(mod, 'get_{}_data'.format(service))

    try:
        bin_name = getattr(mod, 'BINNAME')
    except AttributeError:
        bin_name = None

    return get_data_func, discovery_func, bin_name
