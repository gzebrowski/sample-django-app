# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0009_auto_20150706_1816'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='data_error',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='image_error',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='marked',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AlterIndexTogether(
            name='product',
            index_together=set([('source', 'data_hash'), ('file_avaliable', 'availability', 'image_error'), ('in_collection', 'country', 'file_avaliable', 'availability'), ('data_error', 'availability')]),
        ),
    ]
