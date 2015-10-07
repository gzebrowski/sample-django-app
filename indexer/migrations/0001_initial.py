# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('add_time', models.DateTimeField(auto_now_add=True)),
                ('log_type', models.SmallIntegerField(default=1, choices=[(1, b'info'), (2, b'warning'), (3, b'exception'), (4, b'terminating exception')])),
                ('log', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='SolrInstances',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('str_connection', models.CharField(max_length=128, verbose_name='string connection')),
            ],
        ),
        migrations.CreateModel(
            name='WorkingTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('status', models.SmallIntegerField(default=0, editable=False, choices=[(0, b'new'), (1, b'in progress'), (2, b'finished'), (7, b'awaiting'), (3, b'canceling'), (4, b'canceled'), (5, b'failed'), (6, b'terminated')])),
                ('end_time', models.DateTimeField(null=True, editable=False, blank=True)),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('items_processed', models.IntegerField(default=0, editable=False)),
                ('items_to_process', models.IntegerField(null=True, editable=False, blank=True)),
                ('system_pid', models.IntegerField(null=True, editable=False, blank=True)),
                ('follow_by', models.ForeignKey(blank=True, to='indexer.WorkingTask', null=True)),
                ('solr_instances', models.ManyToManyField(to='indexer.SolrInstances', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='WorkType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('command', models.CharField(max_length=1024)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.AddField(
            model_name='workingtask',
            name='work_type',
            field=models.ForeignKey(to='indexer.WorkType'),
        ),
        migrations.AddField(
            model_name='log',
            name='task',
            field=models.ForeignKey(to='indexer.WorkingTask'),
        ),
    ]
