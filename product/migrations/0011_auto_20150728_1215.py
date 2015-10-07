# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0010_auto_20150714_1948'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image_proc_error',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterIndexTogether(
            name='product',
            index_together=set([('source', 'data_hash'), ('file_avaliable', 'availability', 'image_error'), ('file_avaliable', 'availability', 'image_proc_error'), ('in_collection', 'country', 'file_avaliable', 'availability'), ('data_error', 'availability')]),
        ),
    ]
