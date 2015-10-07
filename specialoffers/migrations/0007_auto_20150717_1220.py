# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('specialoffers', '0006_auto_20150717_1216'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extraclass',
            name='key',
            field=models.SlugField(),
        ),
    ]
