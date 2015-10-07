# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_auto_20150704_0646'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='country',
            field=models.SmallIntegerField(db_index=True, choices=[(1, b'UK'), (2, b'USA')]),
        ),
        migrations.AlterIndexTogether(
            name='product',
            index_together=set([('source', 'data_hash'), ('file_avaliable', 'availability'), ('in_collection', 'country', 'file_avaliable', 'availability')]),
        ),
    ]
