# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('specialoffers', '0004_auto_20150610_1544'),
    ]

    operations = [
        migrations.AddField(
            model_name='specialoffer',
            name='conditions',
            field=models.CharField(max_length=1024, blank=True),
        ),
    ]
