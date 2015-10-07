# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('specialoffers', '0003_specialoffer_shop_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='specialoffer',
            name='discount_code',
            field=models.CharField(max_length=40, null=True, blank=True),
        ),
    ]
