# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0013_auto_20150803_2101'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='in_collection',
            field=models.SmallIntegerField(default=0, blank=True, choices=[(0, b'No'), (1, b'1'), (2, b'2'), (3, b'3')]),
        ),
    ]
