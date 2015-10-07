# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0002_auto_20150612_1843'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profileuser',
            name='gender',
            field=models.CharField(blank=True, max_length=1, null=True, choices=[(b'1', b'Male'), (b'2', b'Female')]),
        ),
    ]
