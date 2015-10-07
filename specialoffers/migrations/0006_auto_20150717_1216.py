# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('specialoffers', '0005_specialoffer_conditions'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtraClass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('key', models.CharField(max_length=32)),
                ('description', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='specialoffer',
            name='extra_class',
            field=models.ForeignKey(blank=True, to='specialoffers.ExtraClass', null=True),
        ),
    ]
