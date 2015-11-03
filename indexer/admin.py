# -*- coding: utf-8 -*-

import os
import datetime
from django.contrib import admin
from django.core.urlresolvers import reverse
from django import forms
from django.conf import settings

from .models import (SolrInstances, WorkingTask, Log, WorkType,
                     WorkTypeParam, MongoDbSource)
from django.utils.html import format_html


@admin.register(SolrInstances)
class SolrInstancesAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'str_connection']


class WorkTypeParamInline(admin.TabularInline):
    model = WorkTypeParam
    fields = ['name', 'param']


@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    inlines = [WorkTypeParamInline]


@admin.register(MongoDbSource)
class MongoDbSourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'host', 'port', 'db', 'collection']


class CurrentDateTimeWidget(admin.widgets.AdminSplitDateTime):
    def format_output(self, rendered_widgets):
        result = super(CurrentDateTimeWidget, self).format_output(rendered_widgets)
        return format_html('<p class="curr-time">Now is: %s</p><br />%s' % (
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), result))


class WorkingTasForm(forms.ModelForm):
    NODE_CHOICES = tuple([(x['id'], x['name']) for x in settings.DISTRIBUTED_SERVERS])
    extra_options = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=(), required=False)
    nodes = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=NODE_CHOICES, required=False, initial=settings.DISTRIBUTED_SERVER_ID)
    start_from_last_point = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(WorkingTasForm, self).__init__(*args, **kwargs)
        self.fields['follow_by'].queryset = WorkingTask.objects.filter(status__in=(
            WorkingTask.STATUS_AWAITING, WorkingTask.STATUS_IN_PROGRESS, WorkingTask.STATUS_NEW))
        self.fields['extra_options'].choices = [("%s:%s" % (choice.work_type.id, choice.id), "task:%s (%s) - %s" % (choice.work_type.id, choice.work_type.name, choice.name)) for choice in WorkTypeParam.objects.all()]
        self.fields['scheduled_for'].widget = CurrentDateTimeWidget()

    def save(self, commit=True):
        obj = super(WorkingTasForm, self).save(commit=False)
        options = self.cleaned_data.get('extra_options')
        extra_options = []
        if options:
            for opt in options:
                tsk, param_id = map(int, opt.split(':'))
                extra_options.append(WorkTypeParam.objects.get(pk=param_id, work_type_id=tsk).param)
            obj.extra_options = ' '.join(extra_options)
        # self.cleaned_data.get('extra_options') [u'1:5', u'1:6']
        nodes = self.cleaned_data.get('nodes')
        if self.cleaned_data.get('start_from_last_point'):
            obj.items_processed = 1
        if nodes:
            obj.all_nodes = '|'.join(nodes)
        if commit:
            obj.save()
        return obj

    class Meta:
        model = WorkingTask
        exclude = []


@admin.register(WorkingTask)
class WorkingTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'work_type', 'dates_and_times', 'my_status', 'progress', 's_instances', 'task_node', 'my_logs']
    list_filter = ('status', 'solr_instances', 'work_type')
    actions = ['cancel_tasks', 'remove_task']
    radio_fields = {"work_type": admin.VERTICAL}
    form = WorkingTasForm
    fieldsets = (
        (None, {
            'fields': ('work_type', ('nodes', 'start_from_last_point'),
                       'solr_instances', 'mongodb_instance', 'extra_options')
        }),
        ('scheduling', {
            'classes': ('collapse',),
            'fields': ('scheduled_for', 'follow_by')
        }),
    )

    class Media:
        css = {
            "all": ("extraadmin/css/my_styles.css",)
        }
        js = ("extraadmin/js/working_task.js",)

    def dates_and_times(self, obj):
        params = (('scheduled_for', 'scheduled for'), ('start_time', 'started'),
                  ('end_time', 'ended'), ('last_update', 'updated'))
        results = []
        for p in params:
            if p[0] == 'last_update' and (obj.end_time or not obj.start_time):
                continue
            if p[0] != 'scheduled_for' and not obj.start_time:
                continue
            if p[0] == 'scheduled_for' and obj.start_time:
                continue
            val = getattr(obj, p[0], False)
            if val:
                results.append('%s: %s' % (p[1], val.strftime('%Y-%m-%d %H:%M:%S')))
        return '/<br />'.join(results)
    dates_and_times.short_description = 'dates and times'
    dates_and_times.allow_tags = True

    def get_actions(self, *args, **kwargs):
        result = super(WorkingTaskAdmin, self).get_actions(*args, **kwargs)
        if 'delete_selected' in result:
            result.pop('delete_selected')
        return result

    def changelist_view(self, request, **kwargs):
        try:
            all_pids = [int(pid) for pid in os.listdir('/proc') if pid.isdigit()]
        except Exception:
            pass
        else:
            WorkingTask.objects.filter(
                node=settings.DISTRIBUTED_SERVER_ID,
                status__in=(WorkingTask.STATUS_CANCELING,
                            WorkingTask.STATUS_IN_PROGRESS,
                            WorkingTask.STATUS_AWAITING)).exclude(
                                system_pid__in=all_pids).update(
                                    status=WorkingTask.STATUS_TERMINATED)
            WorkingTask.objects.filter(
                node=settings.DISTRIBUTED_SERVER_ID,
                status__in=(WorkingTask.STATUS_NEW,), system_pid__isnull=False).exclude(
                    system_pid__in=all_pids).update(status=WorkingTask.STATUS_TERMINATED)
        return super(WorkingTaskAdmin, self).changelist_view(request, **kwargs)

    def progress(self, obj):
        if obj.items_to_process:
            if obj.status == WorkingTask.STATUS_FINISHED:
                prgs = 100
            else:
                prgs = (100 * obj.items_processed / obj.items_to_process)
            if obj.status == WorkingTask.STATUS_IN_PROGRESS:
                stl = 'position: absolute; top: 0; left: 0; height: 20px; background-color: #88FF88; width: %s%%; z-index: 0;' % prgs
            else:
                stl = ''
            return '<div style="position: relative; width: 100%%;"><div style="%s"></div><div style="z-index: 1; position: relative; left: 0; top: 0; padding: 4px;">%s/%s (%s%%)</div></div>' % (stl, obj.items_processed, obj.items_to_process, prgs)
        else:
            return '0%'
    progress.allow_tags = True

    def s_instances(self, obj):
        instances = list(obj.solr_instances.all().values_list('name', flat=True))
        return ', '.join(instances)
    s_instances.short_description = 'instances'

    def cancel_tasks(self, request, queryset):
        queryset.filter(status=WorkingTask.STATUS_IN_PROGRESS).update(status=WorkingTask.STATUS_CANCELING)
    cancel_tasks.short_description = "stop selected tasks"

    def save_related(self, request, form, formsets, change):
        result = super(WorkingTaskAdmin, self).save_related(request, form, formsets, change)
        if form.instance:
            for inst in form.instance.mychildren.all():
                for si in form.instance.solr_instances.all():
                    inst.solr_instances.add(si)
        return result

    def remove_task(self, request, queryset):
        queryset.filter(status__in=(WorkingTask.STATUS_FINISHED,
                                    WorkingTask.STATUS_CANCELED,
                                    WorkingTask.STATUS_FAILED,
                                    WorkingTask.STATUS_TERMINATED)).delete()
    remove_task.short_description = "remove selected tasks"

    def my_logs(self, obj):
        logs_cnt = obj.log_set.all().count()
        return ('<a href="%s?task__exact=%s">%s log(s)</a>' % (reverse('admin:indexer_log_changelist'), obj.pk, logs_cnt)) if logs_cnt else ''
    my_logs.allow_tags = True

    def my_status(self, obj):
        extra_info = " (for %s)" % obj.follow_by_id if obj.follow_by and obj.status == WorkingTask.STATUS_AWAITING else ''
        return '<div class="status-all status-s%s">%s%s</div>' % (obj.status, obj.get_status_display(), extra_info)
    my_status.allow_tags = True

    def has_change_permission(self, request, obj=None):
        if obj:
            return False
        return super(WorkingTaskAdmin, self).has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj:
            if obj.status in (WorkingTask.STATUS_FINISHED, WorkingTask.STATUS_CANCELED,
                              WorkingTask.STATUS_FAILED) or obj.start_time < (datetime.datetime.now() - datetime.timedelta(days=1)):
                return super(WorkingTaskAdmin, self).has_delete_permission(request, obj=obj)
        return False

    def task_node(self, obj):
        xx = [x['name'] for x in settings.DISTRIBUTED_SERVERS if x['id'] == obj.node]
        return xx[0] if xx else '?'


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ['id', 'task', 'add_time', 'log_type']
    list_filter = ('log_type',)
    date_hierarchy = 'add_time'

    def has_add_permission(self, request):
        return False
