__author__ = 'Harrison'
from Monitor import Monitor
from argh import ArghParser
import argparse

class ServiceMonitor(Monitor):
    def load_data(self, service, instance, is_discovery=False, **kwargs):
        '''

        @param service:
        @param instance:
        @param is_discovery:
        @param kwargs:
        @return:
        '''