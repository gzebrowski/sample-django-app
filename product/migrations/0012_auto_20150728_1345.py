# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0011_auto_20150728_1215'),
    ]

    operations = [
        migrations.CreateModel(
            name='RemovedItems',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('original_url', models.CharField(max_length=255, db_index=True)),
                ('original_url_hash', models.CharField(max_length=40, db_index=True)),
                ('data_hash', models.CharField(max_length=40, db_index=True)),
                ('add_time', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='removeditems',
            unique_together=set([('original_url_hash', 'data_hash')]),
        ),
    ]
