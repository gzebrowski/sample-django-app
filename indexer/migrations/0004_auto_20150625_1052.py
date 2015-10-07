# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indexer', '0003_workingtask_extra_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='MongoDbSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('host', models.CharField(max_length=128)),
                ('port', models.IntegerField(default=27017, blank=True)),
                ('db', models.CharField(max_length=128)),
                ('collection', models.CharField(max_length=128)),
                ('record_processor', models.CharField(max_length=128, null=True, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='workingtask',
            name='mongodb_instance',
            field=models.ForeignKey(blank=True, to='indexer.MongoDbSource', null=True),
        ),
    ]
