# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='MainCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('external_db_id', models.CharField(max_length=255, null=True, blank=True)),
                ('country', models.SmallIntegerField(choices=[(1, b'UK'), (2, b'USA')])),
                ('product_name', models.CharField(max_length=255)),
                ('product_description', models.TextField(null=True, blank=True)),
                ('product_img', models.CharField(max_length=255)),
                ('price', models.FloatField()),
                ('price_max', models.FloatField(null=True, blank=True)),
                ('original_price', models.FloatField(null=True, blank=True)),
                ('original_price_max', models.FloatField(null=True, blank=True)),
                ('product_category', models.CharField(max_length=128, null=True, blank=True)),
                ('size', models.CharField(max_length=1024, null=True, blank=True)),
                ('product_colors', models.CharField(max_length=255, null=True, blank=True)),
                ('original_url', models.CharField(unique=True, max_length=255)),
                ('crawl_date', models.DateTimeField(null=True, blank=True)),
                ('product_id', models.IntegerField(unique=True, null=True, blank=True)),
                ('availability', models.BooleanField(default=True)),
                ('outdated', models.DateTimeField(null=True, blank=True)),
                ('data_hash', models.CharField(max_length=40, blank=True)),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('relative_img_path', models.CharField(max_length=280)),
                ('file_avaliable', models.BooleanField(default=False)),
                ('brand', models.ForeignKey(to='product.Brand')),
                ('main_category', models.ManyToManyField(to='product.MainCategory')),
            ],
        ),
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='shop',
            field=models.ForeignKey(to='product.Shop'),
        ),
        migrations.AlterIndexTogether(
            name='product',
            index_together=set([('file_avaliable', 'availability')]),
        ),
    ]
