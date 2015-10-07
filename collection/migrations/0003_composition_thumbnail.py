# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import collection.models


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0002_composition_compositionelement'),
    ]

    operations = [
        migrations.AddField(
            model_name='composition',
            name='thumbnail',
            field=models.ImageField(null=True, upload_to=collection.models.get_image_path2, blank=True),
        ),
    ]
