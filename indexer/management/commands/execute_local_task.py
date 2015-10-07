# -*- coding: utf-8 -*-

import datetime
import os
from django.core.management.base import BaseCommand
from indexer.models import WorkingTask
from django.conf import settings
from optparse import make_option
from subprocess import Popen


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-i', '--idtask',
                    dest='idtask',
                    type='int',
                    help='ID of the task'),)

    def handle(self, *args, **options):
        task_id = int(options['idtask'])
        instance = WorkingTask.objects.get(pk=task_id)
        cmd, params = (instance.work_type.command + ' ').split(' ', 1)
        manage_path = os.path.join(settings.BASE_DIR, 'manage.py')
        extra_options = instance.extra_options or ''
        cmd = "%s %s %s --idtask=%s %s %s" % (settings.PYTHON_PATH, manage_path, cmd, instance.pk, params, extra_options)
        proc = Popen(filter(None, [c.strip() for c in cmd.strip().split()]))
        instance.system_pid = proc.pid
        if not instance.scheduled_for and not instance.follow_by:
            instance.start_time = datetime.datetime.now()
        instance.save()
