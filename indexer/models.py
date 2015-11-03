# -*- coding: utf-8 -*-

import os
from subprocess import Popen
from django.db import models
from django.db.models import signals
from django.conf import settings
import logging
logger = logging.getLogger('solrindexer')


class WorkType(models.Model):
    name = models.CharField(max_length=64)
    command = models.CharField(max_length=1024)
    run_synchronously = models.BooleanField(default=True, blank=True, help_text="If executed on many nodes - whether this task should work synchronously or asynchronously")
    multiinstance_allowed = models.BooleanField(default=True, blank=True, help_text="Is executing on many nodes allowed")

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class WorkTypeParam(models.Model):
    VALUE_TYPE_NONE = 0
    VALUE_TYPE_TEXT = 1
    VALUE_TYPE_INT = 2
    VALUE_TYPE_CHOICE = 3
    VALUE_TYPE_CHOICES = (
        (VALUE_TYPE_NONE, u'None'),
        (VALUE_TYPE_TEXT, u'text'),
        (VALUE_TYPE_INT, u'Int'),
        (VALUE_TYPE_CHOICE, u'Choice'),
    )
    work_type = models.ForeignKey(WorkType)
    name = models.CharField(max_length=128)
    param = models.CharField(max_length=128)
    value_type = models.SmallIntegerField(default=VALUE_TYPE_NONE,
                                          choices=VALUE_TYPE_CHOICES,
                                          null=True, blank=True)

    class Meta:
        ordering = ('work_type', 'id')

    def __unicode__(self):
        return self.name


class SolrInstances(models.Model):
    name = models.CharField(max_length=128)
    str_connection = models.CharField(max_length=128, verbose_name=u'string connection')

    def __unicode__(self):
        return self.name


class MongoDbSource(models.Model):
    name = models.CharField(max_length=128)
    host = models.CharField(max_length=128)
    port = models.IntegerField(default=27017, blank=True)
    db = models.CharField(max_length=128)
    collection = models.CharField(max_length=128)
    record_processor = models.CharField(max_length=128, blank=True, null=True)

    def __unicode__(self):
        return self.name


class WorkingTask(models.Model):
    STATUS_NEW = 0
    STATUS_IN_PROGRESS = 1
    STATUS_FINISHED = 2
    STATUS_CANCELING = 3
    STATUS_CANCELED = 4
    STATUS_FAILED = 5
    STATUS_TERMINATED = 6
    STATUS_AWAITING = 7
    STATUS_CHOICES = ((STATUS_NEW, 'new'),
                      (STATUS_IN_PROGRESS, 'in progress'),
                      (STATUS_FINISHED, 'finished'),
                      (STATUS_AWAITING, 'awaiting'),
                      (STATUS_CANCELING, 'canceling'),
                      (STATUS_CANCELED, 'canceled'),
                      (STATUS_FAILED, 'failed'),
                      (STATUS_TERMINATED, 'terminated'))

    work_type = models.ForeignKey(WorkType)
    parent = models.ForeignKey('self', null=True, blank=True, editable=False, related_name='mychildren')
    start_time = models.DateTimeField(null=True, blank=True, editable=False)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    status = models.SmallIntegerField(default=STATUS_NEW, choices=STATUS_CHOICES, editable=False)
    end_time = models.DateTimeField(null=True, blank=True, editable=False)
    last_update = models.DateTimeField(auto_now=True)
    items_processed = models.IntegerField(default=0, editable=False)
    items_to_process = models.IntegerField(null=True, blank=True, editable=False)
    solr_instances = models.ManyToManyField(SolrInstances, blank=True)
    mongodb_instance = models.ForeignKey(MongoDbSource, blank=True, null=True)
    system_pid = models.IntegerField(null=True, blank=True, editable=False)
    follow_by = models.ForeignKey('self', null=True, blank=True)
    extra_options = models.CharField(max_length=1024, null=True, blank=True, editable=False)
    node = models.CharField(max_length=16, null=True, blank=True, editable=False)
    all_nodes = models.CharField(max_length=1024, null=True, blank=True, editable=False)

    def __unicode__(self):
        return "task %s at %s" % (self.work_type, self.start_time)


class Log(models.Model):
    LOGTYPE_INFO = 1
    LOGTYPE_WARNING = 2
    LOGTYPE_EXCEPTION = 3
    LOGTYPE_TERMINATING_EXCEPTION = 4
    LOGTYPE_CHOICES = ((LOGTYPE_INFO, 'info'),
                       (LOGTYPE_WARNING, 'warning'),
                       (LOGTYPE_EXCEPTION, 'exception'),
                       (LOGTYPE_TERMINATING_EXCEPTION, 'terminating exception'))
    task = models.ForeignKey(WorkingTask)
    add_time = models.DateTimeField(auto_now_add=True)
    log_type = models.SmallIntegerField(default=LOGTYPE_INFO, choices=LOGTYPE_CHOICES)
    log = models.TextField()

    def __unicode__(self):
        return "log id: %s to %s" % (self.pk, unicode(self.task))


# @receiver(signals.post_save, WorkingTask)
def indexing_task_saved(sender, instance, created, *args, **kwargs):
    if created and not instance.node:
        is_synchronus = instance.work_type.run_synchronously
        if '--run-synchronously' in (instance.extra_options or ''):
            is_synchronus = True
            instance.extra_options = instance.extra_options.replace('--run-synchronously', '')
        nodes = instance.all_nodes.split('|') if instance.all_nodes else [settings.DISTRIBUTED_SERVER_ID]
        manage_path = os.path.join(settings.BASE_DIR, 'manage.py')
        cmd = "execute_local_task"
        cmd = "%s %s %s --idtask=%%s" % (settings.PYTHON_PATH, manage_path, cmd)
        node_list = [(s['id'], s['IP']) for s in settings.DISTRIBUTED_SERVERS]
        node_dict = dict(node_list)
        quote_cmd = cmd.replace('"', '\\"')
        attrs2copy = ['work_type', 'scheduled_for', 'mongodb_instance', 'extra_options'] + ['follow_by']
        last_id = None
        wt = instance
        items_processed = instance.items_processed
        if not instance.work_type.multiinstance_allowed:
            nodes = nodes[:1]
        for nr, node in enumerate(nodes):
            if nr > 0:
                wt = WorkingTask(node=node)  # set node to protect from executing this signal
                for a in attrs2copy:
                    setattr(wt, a, getattr(instance, a))
                wt.save()
                for si in instance.solr_instances.all():
                    wt.solr_instances.add(si)
                wt.parent = instance
            if items_processed > 0:
                prev_qset = WorkingTask.objects.filter(node=node).exclude(pk=wt.id).order_by('-id')
                if prev_qset:
                    wt.items_processed = prev_qset[0].items_processed
            if settings.DISTRIBUTED_SERVER_ID == node:
                cmd2 = (cmd % wt.pk).strip().split()
            else:
                cmd2 = ('%s -m %s' % (settings.DSH_PATH, node_dict[node])).strip().split() + ['%s --settings=solrindexer.distrib_settings' % (quote_cmd % wt.pk)]
            wt.node = node  # set node once again in case it is not set
            if is_synchronus and last_id:
                wt.follow_by_id = last_id
            wt.save()
            last_id = wt.id
            logger.debug('executing command: %s' % cmd2)
            proc = Popen(filter(None, [c.strip() for c in cmd2]))  # noqa

signals.post_save.connect(indexing_task_saved, WorkingTask)
