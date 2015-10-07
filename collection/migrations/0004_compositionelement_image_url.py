# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import collection.models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0003_composition_thumbnail'),
    ]

    operations = [
        migrations.AddField(
            model_name='compositionelement',
            name='image_url',
            field=collection.models.MyValueCharField(max_length=255, verbose_name=b'image src', blank=True),
        ),
    ]
