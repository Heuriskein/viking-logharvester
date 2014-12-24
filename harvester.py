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
now = str(datetime.datetime.utcnow())

for d, dirs, files in os.walk('/opt/vikinggameserver/logs/'): #   development/port/log
    log = []
    core = []
    for f in files:
        if f.endswith('.core'):
            core.append(f)

        if f.endswith('.log'):
            log.append(f)

    remainder, port = os.path.split(d)
    remainder, branch = os.path.split(remainder)
    core_switch = 'nocrash'
    if len(core) > 0:
        core_switch = 'crash'

    for log_i in xrange(len(log)):
        logkeyname = posixpath.join('logs', branch, core_switch, now, my_id, port, 'log-{}'.format(log_i))
        logkey = bucket.new_key(logkeyname)
        logkey.set_contents_from_filename(os.path.join(d, log[log_i]))

    for core_i in xrange(len(core)):
        corekeyname = posixpath.join('logs', branch, core_switch, now, my_id, port, 'core-{}'.format(core_i))
        corekey = bucket.new_key(corekeyname)
        corekey.set_contents_from_filename(os.path.join(d, core[core_i]))