# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('collection', '0006_auto_20150609_1318'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patternelement',
            name='blur',
        ),
        migrations.RemoveField(
            model_name='patternelement',
            name='color_shadow',
        ),
        migrations.RemoveField(
            model_name='patternelement',
            name='h_shadow',
        ),
        migrations.RemoveField(
            model_name='patternelement',
            name='spread',
        ),
        migrations.RemoveField(
            model_name='patternelement',
            name='v_shadow',
        ),
    ]
