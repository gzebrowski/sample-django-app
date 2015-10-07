# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('collection', '0008_lastusercocomposition'),
    ]

    operations = [
        migrations.AddField(
            model_name='lastusercocomposition',
            name='author',
            field=models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL, verbose_name=b'author'),
        ),
    ]
