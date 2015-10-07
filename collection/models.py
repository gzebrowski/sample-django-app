# -*- coding: utf-8 -*-

import re
import math
import urllib2
from PIL import Image, ImageFont, ImageDraw
import cStringIO
from StringIO import StringIO
import logging

from django.db import models
from django.conf import settings

from django.core.files.storage import get_storage_class, File
from django.utils.text import slugify
from utils.utils import get_image_path, _calc_max_width_height, _calc_size_min

global_storage = get_storage_class(settings.GLOBAL_FILE_STORAGE)()
logger = logging.getLogger('solrindexer')


def get_image_path2(instance, filename):
    extra_path = 'collection/compositions/%s/' % (instance.id or 0)
    return get_image_path(instance, filename, extra_path=extra_path)


def get_image_path3(instance, filename):
    extra_path = 'collection/pattern/%s/' % (instance.id or 0)
    return get_image_path(instance, filename, extra_path=extra_path)


def prepare_product_url(product):
    # temporary to keep compatibility with flask application
    return '/product/%s/%s,%s.html' % (product.get('brand_slug', slugify(product.get('product_brand', '-'))), product.get('product_title_slug', slugify(product['product_name'])), product.get('product_id', '0'))


class MyValueField(object):
    pass

my_value_fields = lambda model_name: [f.name for f in model_name._meta.fields if isinstance(f, MyValueField)]


class MyValueIntegerField(MyValueField, models.IntegerField):
    @classmethod
    def value_retriever(cls):
        return int


class MyValueCharField(MyValueField, models.CharField):
    @classmethod
    def value_retriever(cls):
        return lambda x: unicode(x) if x is not None else None


class MyValueFloatField(MyValueField, models.FloatField):
    @classmethod
    def value_retriever(cls):
        return float


class MyValueForeignKey(MyValueField, models.ForeignKey):
    @classmethod
    def value_retriever(cls):
        return lambda x: x.id


class MyMath(object):
    @classmethod
    def _get_offset_x(cls, width, height, angle):
        half_w = width / 2.0
        half_h = height / 2.0
        c = math.sqrt(half_w * half_w + half_h * half_h)
        curr_angle = (180 / (math.pi / math.atan(half_h / half_w)))
        angle2 = curr_angle - angle
        return abs(int(math.ceil(c * math.cos(math.pi * angle2 / 180.0))))

    @classmethod
    def _get_offset_y(cls, width, height, angle):
        half_w = width / 2.0
        half_h = height / 2.0
        c = math.sqrt(half_w * half_w + half_h * half_h)
        curr_angle = (180 / (math.pi / math.atan(half_w / half_h)))
        angle2 = curr_angle - angle
        return abs(int(math.ceil(c * math.cos(math.pi * angle2 / 180.0))))

    @classmethod
    def get_bounds(cls, left, top, width, height, angle):
        max_right = left + width / 2 + cls._get_offset_x(width, height, angle)
        max_bottom = top + height / 2 + cls._get_offset_y(width, height, angle)
        return (max_right, max_bottom)


class Pattern(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='author', editable=False)
    name = models.CharField(verbose_name='collection name', max_length=255)
    add_time = models.DateTimeField(auto_now_add=True, verbose_name='add time', editable=False)
    active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, blank=True)
    thumbnail = models.ImageField(upload_to=get_image_path3, blank=True, null=True, storage=global_storage)

    def __unicode__(self):
        return u"%s" % self.name

    @property
    def my_thumbnail(self):
        return self.thumbnail.url if self.thumbnail else ''

    def get_patterns_as_json(self):
        els = self.patternelement_set.all()
        result = []
        pattern_fields = my_value_fields(PatternElement)
        for pattern_el in els:
            curr_item = dict([(f, getattr(pattern_el, f)) for f in pattern_fields])
            result.append(curr_item)
        return result

    def create_thumbnail(self, width=None, height=None):
        elements = self.get_patterns_as_json()
        elements.sort(cmp=lambda x, y: cmp(x['z_index'], y['z_index']))
        if not width or not height:
            max_width = 0
            max_height = 0
            for el in elements:
                bounds = MyMath.get_bounds(el['left'], el['top'], el['width'], el['height'], el['rotation'])
                if max_width < bounds[0]:
                    max_width = bounds[0]
                if max_height < bounds[1]:
                    max_height = bounds[1]
            width, height = int(max_width * 1.1), int(max_height * 1.1)
        dest_img = Image.new("RGBA", (width, height), "rgb(255,255,255)")
        dest_img.putalpha(1)
        try:
            font = ImageFont.truetype(settings.DRAW_TEXT_FONT, 18)
        except Exception:
            logger.error("Couldn't use font from settings.DRAW_TEXT_FONT: %s" % getattr(settings, 'DRAW_TEXT_FONT', None))
            font = None
        for el in elements:
            curr_img = Image.new("RGBA", (el['width'], el['height']), "rgb(200,200,200)")
            draw = ImageDraw.Draw(curr_img)
            draw.rectangle((1, 1, el['width'] - 1, el['height'] - 1), fill="rgb(255,240,200)", outline="rgb(128,128,128)")
            if font and el['label']:
                w, h = draw.textsize(el['label'], font=font)
                draw.text((max(0, el['width'] - w) / 2, max(0, el['height'] - h) / 2), el['label'], fill="black")
            bounds = MyMath.get_bounds(0, 0, el['width'], el['height'], el['rotation'])
            final_left = el['left'] - (bounds[0] - el['width']) / 2
            final_top = el['top'] - (bounds[1] - el['height']) / 2
            if el['rotation']:
                curr_img = curr_img.rotate(-el['rotation'], Image.BICUBIC, expand=True)
            dest_img.paste(curr_img, (final_left, final_top), curr_img)
        pixels = dest_img.load()
        width, height = dest_img.size
        for x in xrange(width):
            for y in xrange(height):
                r, g, b, a = pixels[x, y]
                if a == 0:
                    pixels[x, y] = (255, 255, 255, 255)
        dest_img = dest_img.convert('RGB')
        new_size = _calc_size_min(dest_img.size, 200)
        dest_img = dest_img.resize(new_size, Image.ANTIALIAS)
        dest_buff = StringIO()
        dest_img.save(dest_buff, 'JPEG')
        dest_buff.seek(0)
        if getattr(settings, 'LOCAL_PATH_FILE_SAVE', False):
            dest_img.save('%s/final_%s.png' % (settings.LOCAL_PATH_FILE_SAVE, self.id), 'PNG')
        else:
            self.thumbnail.save("%s_%s.jpg" % (slugify(self.name), self.id), File(dest_buff))


class PatternElement(models.Model):
    pattern = models.ForeignKey(Pattern)
    left = MyValueIntegerField(default=0, blank=True)
    top = MyValueIntegerField(default=0, blank=True)
    width = MyValueIntegerField(default=100, blank=True)
    height = MyValueIntegerField(default=150, blank=True)
    rotation = MyValueIntegerField(default=0, blank=True)
    z_index = MyValueIntegerField(default=1, blank=True)
    label = MyValueCharField(max_length=20, blank=True)
    background_image = MyValueCharField(max_length=20, blank=True)
    opacity_image = MyValueFloatField(default=1.0)

    def __unicode__(self):
        return u"%s. %s" % (self.id, getattr(self.pattern, 'name', ''))


class Composition(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='author', editable=False)
    pattern = models.ForeignKey(Pattern)
    thumbnail = models.ImageField(upload_to=get_image_path2, blank=True, null=True, storage=global_storage)
    name = models.CharField(verbose_name='composition name', max_length=255)
    add_time = models.DateTimeField(auto_now_add=True, verbose_name='add time', editable=False)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

    def get_elements_as_json(self):
        els = self.compositionelement_set.all()
        result = []
        pattern_fields = my_value_fields(PatternElement)
        composition_fields = my_value_fields(CompositionElement)
        for el in els:
            pattern_el = el.pattern_element
            curr_item = dict([(f, getattr(pattern_el, f)) for f in pattern_fields])
            image_obj = dict([(f[len('image_'):], getattr(el, f)) for f in composition_fields])
            curr_item['image'] = image_obj
            result.append(curr_item)
        return result

    def create_thumbnail(self, width=None, height=None):
        elements = self.get_elements_as_json()
        elements.sort(cmp=lambda x, y: cmp(x['z_index'], y['z_index']))
        if not width or not height:
            max_width = 0
            max_height = 0
            for el in elements:
                bounds = MyMath.get_bounds(el['left'], el['top'], el['width'], el['height'], el['rotation'])
                if max_width < bounds[0]:
                    max_width = bounds[0]
                if max_height < bounds[1]:
                    max_height = bounds[1]
            width, height = max_width, max_height
        dest_img = Image.new("RGBA", (width, height), "rgb(255,255,255)")
        dest_img.putalpha(1)
        for el in elements:
            bounds = MyMath.get_bounds(0, 0, el['width'], el['height'], el['rotation'])
            final_left = el['left'] - (bounds[0] - el['width']) / 2
            final_top = el['top'] - (bounds[1] - el['height']) / 2
            url = el.get('image', {}).get('src')
            if not url:
                continue
            if url.startswith('//'):
                url = 'http:' + url
            try:
                if re.search('^https?://', url, re.I):
                    content = urllib2.urlopen(url).read()
                else:
                    content = global_storage.open(url).read()
            except Exception:
                raise
            curr_img = Image.open(cStringIO.StringIO(content))
            new_size = _calc_max_width_height(curr_img.size, el['width'], el['height'])
            if int(el['image']['scale'] * 20.0) != 20:
                new_size = (int(new_size[0] * el['image']['scale']), int(new_size[1] * el['image']['scale']))
            if new_size != curr_img.size:
                curr_img = curr_img.resize(new_size, Image.ANTIALIAS)
            if int(el['image']['scale'] * 20.0) != 20 or el['image']['offset_x'] or el['image']['offset_y']:
                crop_params = [(new_size[0] - el['width']) / 2 - el['image']['offset_x'],
                               (new_size[1] - el['height']) / 2 - el['image']['offset_y']]
                img_bckg = Image.new("RGBA", (abs(crop_params[0]) + el['width'], abs(crop_params[1]) + el['height']), "rgb(255,255,255)")
                img_bckg.putalpha(1)
                paste_x, paste_y = 0, 0
                if crop_params[0] < 0:
                    paste_x = -crop_params[0]
                    crop_params[0] = 0
                if crop_params[1] < 0:
                    paste_y = -crop_params[1]
                    crop_params[1] = 0
                img_bckg.paste(curr_img, (paste_x, paste_y))
                curr_img = img_bckg.crop((crop_params[0], crop_params[1], crop_params[0] + el['width'], crop_params[1] + el['height']))
            if el['rotation']:
                curr_img = curr_img.rotate(-el['rotation'], Image.BICUBIC, expand=True)
            dest_img.paste(curr_img, (final_left, final_top), curr_img)
        pixels = dest_img.load()
        width, height = dest_img.size
        for x in xrange(width):
            for y in xrange(height):
                r, g, b, a = pixels[x, y]
                if a == 0:
                    pixels[x, y] = (255, 255, 255, 255)
        dest_img = dest_img.convert('RGB')
        new_size = _calc_size_min(dest_img.size, 200)
        dest_img = dest_img.resize(new_size, Image.ANTIALIAS)
        dest_buff = StringIO()
        dest_img.save(dest_buff, 'JPEG')
        dest_buff.seek(0)
        self.thumbnail.save("%s_%s.jpg" % (slugify(self.name), self.id), File(dest_buff))
        # dest_img.save('e:/final_%s.png' % self.id, 'PNG')


class CompositionElement(models.Model):
    composition = models.ForeignKey(Composition)
    pattern_element = models.ForeignKey(PatternElement)
    image_width = MyValueIntegerField()
    image_height = MyValueIntegerField()
    image_scale = MyValueFloatField(default=1.0)
    image_offset_x = MyValueIntegerField(default=0)
    image_offset_y = MyValueIntegerField(default=0)
    image_dbid = MyValueIntegerField()
    image_src = MyValueCharField(verbose_name='image src', max_length=255, blank=True)
    image_url = MyValueCharField(verbose_name='product url', max_length=255, blank=True)

    def __unicode__(self):
        return "element %s of %s" % (self.id, getattr(self.composition, 'name', ''))


class LastUserCoComposition(models.Model):
    "Caching table"
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='author', editable=False)
    composition_ids = models.CharField(default='', max_length=64, blank=True, editable=False)
    last_created = models.DateTimeField(null=True, db_index=True)

    class Meta:
        ordering = ('-last_created',)

    def __unicode__(self):
        return "Composition of %s at %s" % (self.author, self.created)
