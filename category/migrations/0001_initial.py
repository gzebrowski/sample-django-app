# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(unique=True, max_length=255)),
                ('depth', models.PositiveIntegerField()),
                ('numchild', models.PositiveIntegerField(default=0)),
                ('name', models.CharField(help_text='enter the name of the category', max_length=128, verbose_name='name')),
                ('slug', models.SlugField(max_length=128, verbose_name='slug')),
                ('active', models.BooleanField(default=True, verbose_name='active')),
                ('lead', models.TextField(blank=True)),
                ('keywords', models.CharField(help_text='metatag for SEO purposes', max_length=255, blank=True)),
                ('description', models.CharField(help_text='metatag for SEO purposes', max_length=255, blank=True)),
            ],
            options={
                'ordering': ['path'],
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
        ),
    ]
