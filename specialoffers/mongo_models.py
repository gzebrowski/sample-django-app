# -*- coding: utf-8 -*-

import mongoengine as models
# from utils.utils import FixMultiDbQset


class SpecialOffer(models.Document):
    logo_image = models.StringField(required=False)
    title = models.StringField(max_length=255)
    shop_name = models.StringField(max_length=255, required=False)
    description = models.StringField(max_length=1024)
    end_date = models.DateTimeField(required=False)
    end_date_int = models.IntField(required=False)
    box_size = models.IntField(choices=((1, 'normal'), (2, 'big')))
    shop_url = models.URLField()
    popularity = models.IntField(default=0)
    country = models.IntField(choices=((1, 'UK'), (2, 'USA')))
    ordering = models.IntField(default=0)
    discount_code = models.StringField(max_length=40, required=False)
    conditions = models.StringField(max_length=1024, required=False)
    is_freeshiping = models.BooleanField(default=False, required=False)
    is_discount = models.BooleanField(default=False, required=False)
    db_id = models.IntField(unique=True)
    extra_class = models.StringField(max_length=32, required=False)

    # meta = {
    #    'queryset_class': FixMultiDbQset
    # }
