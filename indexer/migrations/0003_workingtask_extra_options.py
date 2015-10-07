# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('indexer', '0002_worktypeparam'),
    ]

    operations = [
        migrations.AddField(
            model_name='workingtask',
            name='extra_options',
            field=models.CharField(max_length=1024, null=True, editable=False, blank=True),
        ),
    ]
