#!/usr/bin/env python2.7
# -*- coding: utf8 -*-
__author__ = 'Harrison'
import os
import sys
import amqp
from argh import ArghParser, arg
from time import gmtime, strftime

class HandleMQ(object):
    def __init__(self, host, virtual_host='/', userid='guest', passwd='guest'):
        conn = amqp.Connection(host=host, virtual_host=virtual_host, userid=userid, password=passwd)
        self._ch = conn.channel()
        self._exchange_name = '173_alarm_exchange'
        self._ch.exchange_declare(exchange=self._exchange_name, type='direct')

    def producer(self, message_type, message):

        routing_key = message_type

        msg = amqp.Message(message)
        self._ch.basic_publish(self._exchange_name, routing_key, msg)

    def consume(self, message_type, callback):
        queue_name = "{}_{}".format(self._exchange_name, message_type)
        self._ch.queue_declare(queue=queue_name)
        self._ch.queue_bind(queue_name, self._exchange_name)
        self._ch.basic_consume(queue_name, callback=callback, no_ack=True)

        while self._ch.callbacks:
            self._ch.wait()
