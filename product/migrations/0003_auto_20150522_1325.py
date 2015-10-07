# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0002_producttag'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='brand',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='shop',
            options={'ordering': ('name',)},
        ),
    ]
