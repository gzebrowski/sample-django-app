# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indexer', '0004_auto_20150625_1052'),
    ]

    operations = [
        migrations.AddField(
            model_name='workingtask',
            name='scheduled_for',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='workingtask',
            name='start_time',
            field=models.DateTimeField(null=True, editable=False, blank=True),
        ),
    ]
