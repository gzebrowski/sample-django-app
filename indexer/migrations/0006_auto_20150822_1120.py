# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indexer', '0005_auto_20150707_1017'),
    ]

    operations = [
        migrations.AddField(
            model_name='workingtask',
            name='all_nodes',
            field=models.CharField(max_length=1024, null=True, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='workingtask',
            name='node',
            field=models.CharField(max_length=16, null=True, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='worktypeparam',
            name='multiinstance_allowed',
            field=models.BooleanField(default=True, help_text=b'Is executing on many nodes allowed'),
        ),
        migrations.AddField(
            model_name='worktypeparam',
            name='run_synchronously',
            field=models.BooleanField(default=True, help_text=b'If executed on many nodes - whether this task should work synchronously or asynchronously'),
        ),
    ]
