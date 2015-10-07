# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('userprofile', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profileuser',
            name='confirmed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profileuser',
            name='password_hash',
            field=models.CharField(max_length=255, null=True, editable=False, blank=True),
        ),
        migrations.AddField(
            model_name='profileuser',
            name='social_user',
            field=models.CharField(max_length=64, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='profileuser',
            name='social_user_data',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='profileuser',
            name='gender',
            field=models.CharField(blank=True, max_length=1, choices=[(b'1', b'Male'), (b'2', b'Female')]),
        ),
    ]
