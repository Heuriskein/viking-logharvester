#!/usr/bin/python

__author__ = 'Ryan'

import os
import sys
import posixpath
import socket
from boto import connect_s3
import datetime
import time

connection = connect_s3()
bucket = connection.get_bucket('vikinggame-logs')

# This is imperfect, since IPs will be reused. but hopefully the timestamp combined with the IP is sufficient
my_id = socket.gethostbyname(socket.gethostname())
now = str(datetime.datetime.utcnow())

def gather_files():
    logs_to_save = []
    cores_to_save = []
    for d, dirs, files in os.walk('/opt/vikinggameserver/logs/'): #   development/port/log
        log = []
        core = []
        for f in files:
            if f.endswith('.core'):
                # Don't include signal 6 files. These are currently created by the ABRT signal and aren't helpful to us.
                if f.find('SIGNAL:6') == -1:
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
            logkey.set_contents_from_string("<pending>")
            logkey.close()

            logs_to_save.append({
                    'keyname': logkeyname,
                    'filename': os.path.join(d, log[log_i]),
                    'branch': branch,
                    'port': port,
                }
            )

            #logkey.set_contents_from_filename(os.path.join(d, log[log_i]))

        for core_i in xrange(len(core)):
            corekeyname = posixpath.join('logs', branch, core_switch, now, my_id, port, 'core-{}'.format(core_i))
            corekey = bucket.new_key(corekeyname)
            # Save all cores at the end
            corekey.set_contents_from_string("<pending>")
            corekey.close()


            cores_to_save.append({
                'keyname': corekeyname,
                'filename': os.path.join(d, log[log_i]),
                'branch': branch,
                'port': port,
                }
            )
            #corekey.set_contents_from_filename(os.path.join(d, core[core_i]))

    return logs_to_save, cores_to_save

def upload_list(l):
    removes = []
    for i in xrange(len(l)):
        this = l[i]
        if check_stillrunning(port=this['port']):
            print 'Skipping {}, still running'.format(this['filename'])
        else:
            print 'Uploading {}'.format(this['filename'])
            this_key = bucket.get_key(this['keyname'])
            this_key.set_contents_from_filename(this['filename'])
            this_key.close()
            removes.append(i)

    count = 0
    for i in removes:
        del l[i - count]
        count += 1

    return l

def check_stillrunning(port):
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    for pid in pids:
        try:
            path = os.path.join('/proc', pid, 'cmdline')
            value = open(path, 'rb').read()
            if value.find('VikingGameServer\0-pak\0-Port={}'.format(port)) != -1:
                return True
        except KeyboardInterrupt:
            sys.exit('Interrupted by Ctrl-C')
        except:
            continue
    return False

if __name__ == '__main__':
    logs_to_save, cores_to_save = gather_files()
    while len(logs_to_save) > 0:
        logs_to_save = upload_list(logs_to_save)
    while len(cores_to_save) > 0:
        cores_to_save = upload_list(cores_to_save)