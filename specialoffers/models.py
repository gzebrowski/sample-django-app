# -*- coding: utf-8 -*-

# import os
from django.db import models
from django.conf import settings
from django.core.files.storage import get_storage_class
from utils.utils import get_image_path
import logging
logger = logging.getLogger('solrindexer')

global_storage = get_storage_class(settings.GLOBAL_FILE_STORAGE)()


def get_image_path2(instance, filename):
    extra_path = 'special_offer/logos/%s/' % (instance.id or 0)
    return get_image_path(instance, filename, extra_path=extra_path)


class ExtraClass(models.Model):
    name = models.CharField(max_length=255)
    key = models.SlugField()
    description = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return self.name


class SpecialOffer(models.Model):
    logo_image = models.ImageField(upload_to=get_image_path2, blank=True, null=True, storage=global_storage)
    title = models.CharField(max_length=255)
    shop_name = models.CharField(max_length=255)
    description = models.CharField(max_length=1024, blank=True)
    end_date = models.DateField(blank=True, null=True)
    end_date_int = models.IntegerField(blank=True, null=True, editable=False)
    box_size = models.SmallIntegerField(choices=((1, 'normal'), (2, 'big')))
    shop_url = models.URLField()
    popularity = models.IntegerField(default=0, blank=True)
    country = models.SmallIntegerField(choices=((1, 'UK'), (2, 'USA')))
    ordering = models.IntegerField(default=0, blank=True)
    discount_code = models.CharField(max_length=40, blank=True, null=True)
    conditions = models.CharField(max_length=1024, blank=True)
    is_freeshiping = models.BooleanField(default=False, blank=True)
    is_discount = models.BooleanField(default=False, blank=True)
    extra_class = models.ForeignKey(ExtraClass, blank=True, null=True)

    def __unicode__(self):
        return self.title
