# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indexer', '0006_auto_20150822_1120'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='worktypeparam',
            name='multiinstance_allowed',
        ),
        migrations.RemoveField(
            model_name='worktypeparam',
            name='run_synchronously',
        ),
        migrations.AddField(
            model_name='worktype',
            name='multiinstance_allowed',
            field=models.BooleanField(default=True, help_text=b'Is executing on many nodes allowed'),
        ),
        migrations.AddField(
            model_name='worktype',
            name='run_synchronously',
            field=models.BooleanField(default=True, help_text=b'If executed on many nodes - whether this task should work synchronously or asynchronously'),
        ),
    ]
