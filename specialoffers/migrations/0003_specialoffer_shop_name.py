# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('specialoffers', '0002_auto_20150528_1659'),
    ]

    operations = [
        migrations.AddField(
            model_name='specialoffer',
            name='shop_name',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
