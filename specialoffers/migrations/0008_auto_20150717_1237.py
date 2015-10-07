# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('specialoffers', '0007_auto_20150717_1220'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extraclass',
            name='description',
            field=models.CharField(max_length=255, blank=True),
        ),
    ]
