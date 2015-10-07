# -*- coding: utf-8 -*-

from django.db import models
import logging
logger = logging.getLogger('solrindexer')


class Brand(models.Model):
    name = models.CharField(max_length=64)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class Shop(models.Model):
    name = models.CharField(max_length=64)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class MainCategory(models.Model):
    name = models.CharField(max_length=1024)

    def __unicode__(self):
        return self.name


class ProductTag(models.Model):
    tag = models.CharField(max_length=32)

    def __unicode__(self):
        return self.tag


class Product(models.Model):
    external_db_id = models.CharField(max_length=255, blank=True, null=True)
    source = models.ForeignKey('indexer.MongoDbSource', blank=True, null=True, editable=False)
    category = models.ForeignKey('category.Category', blank=True, null=True)
    shop = models.ForeignKey(Shop)
    country = models.SmallIntegerField(choices=((1, 'UK'), (2, 'USA')), db_index=True)
    product_name = models.CharField(max_length=255)
    product_description = models.TextField(null=True, blank=True)
    brand = models.ForeignKey(Brand)
    product_img = models.CharField(max_length=255)
    price = models.FloatField()
    price_max = models.FloatField(null=True, blank=True)
    original_price = models.FloatField(null=True, blank=True)
    original_price_max = models.FloatField(null=True, blank=True)
    main_category = models.ManyToManyField(MainCategory)
    product_category = models.CharField(max_length=128, null=True, blank=True)
    size = models.CharField(max_length=1024, null=True, blank=True)
    product_colors = models.CharField(max_length=255, null=True, blank=True)
    original_url = models.CharField(max_length=255, unique=True)
    crawl_date = models.DateTimeField(blank=True, null=True)
    product_id = models.BigIntegerField(blank=True, null=True, unique=True)
    availability = models.BooleanField(default=True, blank=True)
    outdated = models.DateTimeField(blank=True, null=True)
    data_hash = models.CharField(max_length=40, blank=True)
    last_update = models.DateTimeField(auto_now=True)
    relative_img_path = models.CharField(max_length=280)
    file_avaliable = models.BooleanField(default=False, blank=True)
    in_collection = models.SmallIntegerField(default=0, blank=True, choices=((0, 'No'), (1, '1'), (2, '2'), (3, '3')))
    image_error = models.BooleanField(default=False, blank=True)
    image_proc_error = models.BooleanField(default=False, blank=True)
    data_error = models.BooleanField(default=False, blank=True)
    marked = models.BooleanField(default=False, blank=True, db_index=True)

    class Meta:
        index_together = (('file_avaliable', 'availability', 'image_error'),
                          ('file_avaliable', 'availability', 'image_proc_error'),
                          ('source', 'data_hash'),
                          ('in_collection', 'country', 'file_avaliable', 'availability'),
                          ('data_error', 'availability'),
                          )

    def __unicode__(self):
        return self.original_url


class RemovedItems(models.Model):
    original_url = models.CharField(max_length=255, db_index=True)
    original_url_hash = models.CharField(max_length=40, db_index=True)
    data_hash = models.CharField(max_length=40, db_index=True)
    add_time = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = (('original_url_hash', 'data_hash'),)

    def __unicode__(self):
        return self.original_url
