# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indexer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkTypeParam',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('param', models.CharField(max_length=128)),
                ('value_type', models.SmallIntegerField(default=0, null=True, blank=True, choices=[(0, 'None'), (1, 'text'), (2, 'Int'), (3, 'Choice')])),
                ('work_type', models.ForeignKey(to='indexer.WorkType')),
            ],
            options={
                'ordering': ('work_type', 'id'),
            },
        ),
    ]
