# -*- coding: utf-8 -*-

import mongoengine as models


class Category(models.Document):
    path = models.StringField(max_length=256, required=True)
    depth = models.IntField(required=True)
    numchild = models.IntField(required=True)
    db_id = models.IntField(required=False)
    active = models.BooleanField(default=True)
    name = models.StringField(max_length=128, required=True)
    lead = models.StringField(max_length=2048, required=False)
    slug = models.StringField(max_length=128, required=False)
    keywords = models.StringField(max_length=255, required=False)
    description = models.StringField(max_length=255, required=False)

    def __unicode__(self):
        return self.name
