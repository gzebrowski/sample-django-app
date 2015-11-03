# -*- coding: utf-8 -*-

import os
import time
from solrindexer.settings import DISTRIBUTED_SERVERS
from fabric.api import execute, task, sudo, put
# from fabric.api import env, run
# from fabric.contrib.project import upload_project
from fabric.contrib.project import rsync_project
from fabric.contrib.files import exists

try:
    from local_config import extra_options
except ImportError:
    extra_options = {}

path_join = lambda *x: os.path.join(*x).replace('\\', '/')
REMOTE_APP_DIR = '/home/gz/app/'


def hello():
    # run("sudo ls /etc")
    sudo("ls /etc")


def get_hosts(host=None):
    return ["%s@%s" % (extra_options.get('REMOTE_USER', 'root'), s['IP'])
            for s in DISTRIBUTED_SERVERS if (not host or s['key'] == host)]


def _deploy_project():
    '--rsync-path="sudo rsync"'
    kwargs = extra_options.get('RSYNC_EXTRA_OPTIONS') or {}
    rsync_project(remote_dir=REMOTE_APP_DIR,
                  exclude=['.git'] + extra_options.get('EXCLUDE_FILES', []),
                  **kwargs)


@task
def deploy(host=None):
    hosts = get_hosts(host=host)
    execute(_deploy_project, hosts=hosts)


def _restart():
    for scr in ['dashboard', 'livepanel', 'testpanel']:
        if exists('/etc/init.d/%s' % scr):
            sudo('/etc/init.d/%s stop' % scr)
            time.sleep(3)
            sudo('/etc/init.d/%s start' % scr)


@task
def restart(host=None):
    hosts = get_hosts(host=host)
    execute(_restart, hosts=hosts)


def _update_file(filename=None):
    assert os.path.isfile(filename)
    filename = filename.replace('\\', '/').strip('/')
    put(filename, path_join(REMOTE_APP_DIR, filename), use_sudo=True)


@task
def update_file(filename, host=None):
    hosts = get_hosts(host=host)
    execute(_update_file, hosts=hosts, filename=filename)
