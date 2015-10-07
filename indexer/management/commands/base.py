# -*- coding: utf-8 -*-

import os
import time
import datetime
from indexer.models import WorkingTask, Log
from django.core.management.base import BaseCommand
from django.core.management.base import LabelCommand
from django.conf import settings
from optparse import make_option
import traceback
import logging
logger = logging.getLogger('solrindexer')


class CancelTaskException(Exception):
    pass


class TaskException(Exception):
    pass


class TaskTerminatingException(Exception):
    pass


class TaskCommon(object):
    LOG_PROGRESS_STEP = 100

    def t_handle(self, *args, **options):
        logger.debug('started management')
        self.args = args
        self.options = options
        try:
            self.task = WorkingTask.objects.get(status=WorkingTask.STATUS_NEW, pk=options['idtask'])
            self.wait_for_connected_task()
            self.init()
            self.items_processed = self.task.items_processed
            self.total_items = self.get_total_items()
            self.task.status = WorkingTask.STATUS_IN_PROGRESS
            self.task.items_to_process = self.total_items
            self.task.save()
            self.run_task()
        except CancelTaskException:
            self.add_log('Canceled manually', Log.LOGTYPE_INFO)
            self.task.status = WorkingTask.STATUS_CANCELED
        except TaskTerminatingException:
            self.add_log("parent task didn't succeed", Log.LOGTYPE_TERMINATING_EXCEPTION)
            self.task.status = WorkingTask.STATUS_FAILED
        except Exception:
            self.add_log(traceback.format_exc(), Log.LOGTYPE_TERMINATING_EXCEPTION)
            self.task.status = WorkingTask.STATUS_FAILED
        else:
            self.task.status = WorkingTask.STATUS_FINISHED
        self.task.end_time = datetime.datetime.now()
        self.task.save()
        self.after_finish()

    def after_finish(self):
        pass

    def get_total_items(self):
        return None

    def add_log(self, log, tp=Log.LOGTYPE_INFO):
        Log.objects.create(task=self.task, log_type=tp, log=log)

    def make_progress(self, curr_val):
        self.task.items_processed = curr_val
        tsk = WorkingTask.objects.get(pk=self.task.pk)
        if tsk.status == WorkingTask.STATUS_CANCELING:
            self.task.status == WorkingTask.STATUS_CANCELING
            raise CancelTaskException
        self.task.save()

    def item_processed(self, cnt=1):
        self.items_processed += cnt
        if cnt > 1 or self.items_processed % self.LOG_PROGRESS_STEP == 0:
            self.make_progress(self.items_processed)

    def init(self):
        pass

    def try_to_execute(self, func, args=None, kwargs=None,
                       except_func=None, tryies=5, sleep=10):
        args = args or []
        kwargs = kwargs or {}
        for _try in range(tryies - 1, -1, -1):
            try:
                result = func(*args, **kwargs)
            except Exception:
                if not _try:
                    raise
                if sleep:
                    time.sleep(sleep)
                if except_func and callable(except_func):
                    except_func()
            else:
                return result

    def wait_for_connected_task(self):
        if self.task.follow_by is None and self.task.scheduled_for is None:
            return
        self.task.status = WorkingTask.STATUS_AWAITING
        self.task.save()
        self.dont_check_parent = False

        def wait_for_parent():
            if self.dont_check_parent or self.task.follow_by is None:
                return False
            try:
                parent_task = WorkingTask.objects.get(pk=self.task.follow_by_id)
            except WorkingTask.DoesNotExist:
                raise TaskException
            if parent_task.status == WorkingTask.STATUS_FINISHED:
                self.dont_check_parent = True
                return False
            if parent_task.status in (WorkingTask.STATUS_CANCELED,
                                      WorkingTask.STATUS_FAILED,
                                      WorkingTask.STATUS_TERMINATED):
                raise TaskTerminatingException

            if os.path.isdir('/proc'):
                all_pids = [int(pid) for pid in os.listdir('/proc') if pid.isdigit()]
                if parent_task.node == settings.DISTRIBUTED_SERVER_ID and parent_task.system_pid not in all_pids:
                    raise TaskTerminatingException
            return True

        def wait_for_schedule():
            if self.task.scheduled_for is None:
                return False
            return self.task.scheduled_for > datetime.datetime.now()
        while True:
            if wait_for_schedule() or wait_for_parent():
                time.sleep(10)
            else:
                self.task.start_time = datetime.datetime.now()
                self.task.save()
                break


class TaskCommand(TaskCommon, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-i', '--idtask',
                    dest='idtask',
                    type='int',
                    help='ID of the task'),)

    def handle(self, *args, **options):
        return self.t_handle(*args, **options)


class TaskListCommand(TaskCommon, LabelCommand):
    option_list = BaseCommand.option_list + (
        make_option('-i', '--idtask',
                    dest='idtask',
                    type='int',
                    help='ID of the task'),)

    def handle(self, *args, **options):
        result = self.t_handle(*args, **options)
        return result

    def run_task(self):
        self.orig_handle(*self.args, **self.options)
        return super(TaskListCommand, self).handle(*self.args, **self.options)

    def handle_label(self, label, **options):
        return self.orig_handle_label(label, **options)
