# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import collection.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('collection', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Composition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name=b'composition name')),
                ('add_time', models.DateTimeField(auto_now_add=True, verbose_name=b'add time')),
                ('active', models.BooleanField(default=True)),
                ('author', models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL, verbose_name=b'author')),
                ('pattern', models.ForeignKey(to='collection.Pattern')),
            ],
        ),
        migrations.CreateModel(
            name='CompositionElement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image_width', collection.models.MyValueIntegerField()),
                ('image_height', collection.models.MyValueIntegerField()),
                ('image_scale', collection.models.MyValueFloatField(default=1.0)),
                ('image_offset_x', collection.models.MyValueIntegerField(default=0)),
                ('image_offset_y', collection.models.MyValueIntegerField(default=0)),
                ('image_dbid', collection.models.MyValueIntegerField()),
                ('image_src', collection.models.MyValueCharField(max_length=255, verbose_name=b'image src', blank=True)),
                ('composition', models.ForeignKey(to='collection.Composition')),
                ('pattern_element', models.ForeignKey(to='collection.PatternElement')),
            ],
        ),
    ]
