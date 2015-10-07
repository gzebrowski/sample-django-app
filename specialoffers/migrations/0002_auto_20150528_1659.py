# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('specialoffers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='specialoffer',
            name='description',
            field=models.CharField(max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='specialoffer',
            name='ordering',
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AlterField(
            model_name='specialoffer',
            name='popularity',
            field=models.IntegerField(default=0, blank=True),
        ),
    ]
