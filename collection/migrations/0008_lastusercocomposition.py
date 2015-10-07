# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0007_auto_20150609_1618'),
    ]

    operations = [
        migrations.CreateModel(
            name='LastUserCoComposition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('composition_ids', models.CharField(default=b'', max_length=64, editable=False, blank=True)),
                ('last_created', models.DateTimeField(null=True, db_index=True)),
            ],
            options={
                'ordering': ('-last_created',),
            },
        ),
    ]
