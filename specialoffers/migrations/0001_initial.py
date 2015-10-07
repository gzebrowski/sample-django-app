# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import specialoffers.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SpecialOffer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('logo_image', models.ImageField(null=True, upload_to=specialoffers.models.get_image_path2, blank=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=1024)),
                ('end_date', models.DateField(null=True, blank=True)),
                ('end_date_int', models.IntegerField(null=True, editable=False, blank=True)),
                ('box_size', models.SmallIntegerField(choices=[(1, b'normal'), (2, b'big')])),
                ('shop_url', models.URLField()),
                ('popularity', models.IntegerField(default=0)),
                ('country', models.SmallIntegerField(choices=[(1, b'UK'), (2, b'USA')])),
                ('ordering', models.IntegerField(default=0)),
                ('discount_code', models.CharField(max_length=40)),
                ('is_freeshiping', models.BooleanField(default=False)),
                ('is_discount', models.BooleanField(default=False)),
            ],
        ),
    ]
