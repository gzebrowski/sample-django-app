# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import collection.models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0005_auto_20150605_1729'),
    ]

    operations = [
        migrations.AddField(
            model_name='pattern',
            name='thumbnail',
            field=models.ImageField(null=True, upload_to=collection.models.get_image_path3, blank=True),
        ),
        migrations.AlterField(
            model_name='compositionelement',
            name='image_url',
            field=collection.models.MyValueCharField(max_length=255, verbose_name=b'product url', blank=True),
        ),
    ]
