# -*- coding: utf-8 -*-

import os
import re
import urlparse
# from haystack import indexes
from utils.local_solr import indexes
from .models import Product, ProductTag
from django.template.defaultfilters import slugify

countries_map = {2: 'United States', 1: 'United Kingdom'}

non_accesories_sale = lambda y: (filter(lambda x: x != u'ACCESSORIES' and x != u'SALE', y))


class ProductIndex(indexes.SearchIndex, indexes.Indexable):
    UNIQUE_FIELD = 'pk'

    # text = indexes.CharField(document=True, use_template=True)
    product_title_slug = indexes.CharField()
    product_name = indexes.CharField(model_attr='product_name')
    source_text = indexes.CharField()
    shop_slug = indexes.CharField()
    product_img = indexes.MultiValueField()
    crawl_date = indexes.DateTimeField(model_attr='crawl_date', null=True)
    product_description = indexes.CharField(model_attr='product_description')
    main_category = indexes.MultiValueField()
    category_slug = indexes.MultiValueField()
    country_slug = indexes.CharField()
    country = indexes.CharField()
    pk = indexes.CharField(model_attr='original_url', index_fieldname='id')
    price = indexes.FloatField(model_attr='price')
    price_max = indexes.FloatField()
    original_price = indexes.FloatField(model_attr='original_price', null=True)
    original_price_max = indexes.FloatField(null=True)
    sale_percentage = indexes.MultiValueField(null=True)
    subcategory_slug = indexes.MultiValueField()
    product_category = indexes.MultiValueField()
    product_category_s = indexes.MultiValueField()
    brand_slug = indexes.CharField()
    product_brand = indexes.CharField()
    product_id = indexes.CharField(model_attr='product_id')
    relative_image_filepath = indexes.CharField()
    size = indexes.MultiValueField(null=True)
    product_colors = indexes.MultiValueField(null=True)
    color_slug = indexes.MultiValueField(null=True)
    tag = indexes.MultiValueField(null=True)
    product_colors_text = indexes.MultiValueField(null=True)
    in_collection = indexes.IntegerField(null=True, model_attr='in_collection')
    # product_brand_text = indexes.CharField()

    def __init__(self, *args, **kwargs):
        self.extra_filters = kwargs.get('extra_filters') or {}
        super(ProductIndex, self).__init__(*args, **kwargs)
        self._all_tags = map(unicode.lower, list(ProductTag.objects.all().values_list('tag', flat=True)))

    def get_model(self):
        return Product

    def _prep_categories(self, obj):
        if not hasattr(obj, '_prep_category'):
            res = list(obj.main_category.all().values_list('name', flat=True))
            if 'accessories' in re.split('[^a-z]', unicode(obj.product_category).lower()) and 'ACCESSORIES' not in res:
                res.append(u'ACCESSORIES')
            if obj.original_price and obj.original_price > obj.price:
                res.append(u'SALE')
            obj._prep_category = res
        return obj._prep_category

    def prepare_main_category(self, obj):
        return self._prep_categories(obj)

    def prepare_product_title_slug(self, obj):
        return slugify(obj.product_name)

    def prepare_source_text(self, obj):
        result = obj.shop.name
        if result.lower().endswith('_uk'):
            result = result[:-3]
        return result

    def prepare_shop_slug(self, obj):
        return slugify(self.prepare_source_text(obj))

    def prepare_product_img(self, obj):
        return [obj.product_img]

    def prepare_category_slug(self, obj):
        return [slugify(x) for x in self._prep_categories(obj)]

    def prepare_country_slug(self, obj):
        return slugify(countries_map.get(obj.country, ''))

    def prepare_country(self, obj):
        return countries_map.get(obj.country, '')

    def prepare_price_max(self, obj):
        return obj.price_max or obj.price

    def prepare_original_price_max(self, obj):
        return obj.original_price_max or obj.original_price

    def prepare_sale_percentage(self, obj):
        if obj.original_price or obj.price and obj.original_price > obj.price:
            result = int(100.0 * (obj.original_price - obj.price) / obj.original_price)
            result = (result / 10) * 10
            return map(str, range(10, result + 10, 10))
        return []

    def prepare_subcategory_slug(self, obj):
        return [slugify(x.strip()) for x in self.prepare_product_category(obj)]

    def prepare_product_category(self, obj):
        if u'ACCESSORIES' in re.split('[^A-Z]', unicode(obj.product_category).upper()):
            return non_accesories_sale(self._prep_categories(obj))
        # if obj.product_category.strip().upper() == u'ACCESSORIES':
        return non_accesories_sale([x.strip().upper() for x in obj.product_category.split(',')])

    def prepare_product_category_s(self, obj):
        return [x.strip().upper() for x in self.prepare_product_category(obj)]

    def prepare_brand_slug(self, obj):
        return slugify(obj.brand.name)

    def prepare_product_brand(self, obj):
        return obj.brand.name

    def prepare_relative_image_filepath(self, obj):
        if obj.relative_img_path:
            return obj.relative_img_path
        try:
            parsed = urlparse.urlparse(obj.product_img)
            ext = os.path.splitext(parsed.path)[-1]
            fname = slugify(obj.product_name)[:64]
            val = "%0.10d" % obj.product_id
        except Exception:
            return ''
        else:
            return '%s/%s/%s%s' % (val[:3], val, fname, ext)

    def prepare_size(self, obj):
        return re.split(r'[,;\s]+', obj.size or '')

    def prepare_product_colors(self, obj):
        return filter(None, [c.upper().strip() for c in re.split(r'[,;\s]+', obj.product_colors or '')]) or None

    def prepare_color_slug(self, obj):
        return filter(None, [slugify(c) for c in re.split(r'[,;\s]+', obj.product_colors or '')]) or None

    def prepare_tag(self, obj):
        res = []
        all_text = ' '.join([obj.product_name, obj.product_description, obj.product_category]).lower()
        for t in self._all_tags:
            if t in all_text:
                res.append(t)
        return res

    def prepare_product_colors_text(self, obj):
        return self.prepare_product_colors(obj)

    def prepare_product_brand_text(self, obj):
        return self.prepare_product_brand(obj)

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all().filter(availability=True, **self.extra_filters)


class AutoSuggestionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField()
    text_type = indexes.CharField()

    def get_model(self):
        return Product

    def prepare_text(self, obj):
        return obj.my_text

    def prepare_text_type(self, obj):
        return obj.my_text_type

    def _get_product_name(self, obj):
        return [obj.product_name]

    def _get_product_category(self, obj):
        return [x.strip().upper() for x in obj.product_category.split(',')]

    def _get_main_category(self, obj):
        res = list(obj.main_category.all().values_list('name', flat=True))
        if obj.original_price and obj.original_price > obj.price:
            res.append('SALE')
        return res

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all().filter(availability=True)

    def process_object(self, obj):
        class XObj(object):
            def __init__(self, my_text, my_text_type):
                self.my_text_type = my_text_type
                self.my_text = my_text
        for field in ['product_category', 'main_category', 'product_name']:
            for val in getattr(self, '_get_%s' % field)(obj):
                new_obj = XObj(val, field)
                super(AutoSuggestionIndex, self).process_object(new_obj)
