#!/usr/bin/python

__author__ = 'Ryan'

import os
import posixpath
import socket
from boto import connect_s3
import datetime

connection = connect_s3()
bucket = connection.get_bucket('vikinggame-logs')

# This is imperfect, since IPs will be reused. but hopefully the timestamp combined with the IP is sufficient
my_id = socket.gethostbyname(socket.gethostname())


for d, dirs, files in os.walk('/opt/vikinggameserver/logs/'): #   development/port/log
    log = None
    core = None
    for f in files:
        if f.endswith('.core'):
            core = f

        if f.endswith('.log'):
            log = f

    if log is not None:
        remainder, port = os.path.split(d)
        remainder, branch = os.path.split(remainder)
        now = str(datetime.datetime.utcnow())

        core_switch = 'nocrash'
        if core is not None:
            core_switch = 'crash'
            corekeyname = posixpath.join('logs', branch, core_switch, my_id, port, 'core')
            corekey = bucket.new_key(corekeyname)
            corekey.set_contents_from_filename(os.path.join(d, core))

        logkeyname = posixpath.join('logs', branch, core_switch, my_id, port, now, 'log')
        logkey = bucket.new_key(logkeyname)
        logkey.set_contents_from_filename(os.path.join(d, log))