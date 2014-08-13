# -*- coding: utf-8 -*-
__author__ = 'Harrison'
import multiprocessing
import amqp
import alarm_system.utils.protocol
from functools import partial
from alarm_system.utils import config

class Decoder(multiprocessing.Process):
    def __init__(self, mqinfo, output):
        super(Decoder, self).__init__()
        self.mqinfo = mqinfo
        self.output = output

    @classmethod
    def callback(cls, channle, output, msg):


    def run(self):
        host = self.mqinfo.get('host', '127.0.0.1')
        vhost = self.mqinfo.get('virtual_host', '/')
        userid = self.mqinfo.get('userid', '')
        password = self.mqinfo.get('password', '')
        conn = amqp.Connection(host=host, virtual_host=vhost, userid=userid, password=password)
        ch = conn.channel()
        ch.exchange_declare(exchange='alarm_message', type='fanout')

        qname, _, _ = ch.queue_declare()

        ch.queue_bind(qname, 'alarm_message')

        ch.basic_consume(qname, callback=partial(Decoder.callback, ch, self.output), no_ack=True)
        while ch.callbacks:
            ch.wait()
        ch.close()
        conn.close()

    def decode(self, msg):
