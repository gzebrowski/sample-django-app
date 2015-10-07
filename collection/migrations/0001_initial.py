# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import collection.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Pattern',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name=b'collection name')),
                ('add_time', models.DateTimeField(auto_now_add=True, verbose_name=b'add time')),
                ('active', models.BooleanField(default=True)),
                ('order', models.IntegerField(default=0, blank=True)),
                ('author', models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL, verbose_name=b'author')),
            ],
        ),
        migrations.CreateModel(
            name='PatternElement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('left', collection.models.MyValueIntegerField(default=0, blank=True)),
                ('top', collection.models.MyValueIntegerField(default=0, blank=True)),
                ('width', collection.models.MyValueIntegerField(default=100, blank=True)),
                ('height', collection.models.MyValueIntegerField(default=150, blank=True)),
                ('rotation', collection.models.MyValueIntegerField(default=0, blank=True)),
                ('z_index', collection.models.MyValueIntegerField(default=1, blank=True)),
                ('h_shadow', collection.models.MyValueIntegerField(default=1, blank=True)),
                ('v_shadow', collection.models.MyValueIntegerField(default=1, blank=True)),
                ('blur', collection.models.MyValueIntegerField(default=1, blank=True)),
                ('spread', collection.models.MyValueIntegerField(default=1, blank=True)),
                ('color_shadow', collection.models.MyValueCharField(max_length=9, verbose_name=b'color')),
                ('pattern', models.ForeignKey(to='collection.Pattern')),
            ],
        ),
    ]
