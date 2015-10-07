# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import collection.models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0004_compositionelement_image_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='patternelement',
            name='background_image',
            field=collection.models.MyValueCharField(max_length=20, blank=True),
        ),
        migrations.AddField(
            model_name='patternelement',
            name='label',
            field=collection.models.MyValueCharField(max_length=20, blank=True),
        ),
        migrations.AddField(
            model_name='patternelement',
            name='opacity_image',
            field=collection.models.MyValueFloatField(default=1.0),
        ),
    ]
