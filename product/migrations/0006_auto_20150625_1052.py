# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indexer', '0004_auto_20150625_1052'),
        ('product', '0005_product_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='source',
            field=models.ForeignKey(blank=True, editable=False, to='indexer.MongoDbSource', null=True),
        ),
        migrations.AlterIndexTogether(
            name='product',
            index_together=set([('source', 'data_hash'), ('file_avaliable', 'availability')]),
        ),
    ]
