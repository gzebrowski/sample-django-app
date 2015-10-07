# -*- coding: utf-8 -*-

import datetime
import os
import time
from hashlib import md5
from PIL import Image

from StringIO import StringIO
from django.conf import settings
# from django.template.defaultfilters import slugify
from django.core.files import File
from django.core.files.storage import get_storage_class
from mongoengine.base.fields import BaseField
from mongoengine import QuerySet
from mongoengine.context_managers import switch_db
from hash_ring import HashRing

storage = get_storage_class(settings.SAFE_FILE_STORAGE)()
distrib_servers = [x['id'] for x in settings.DISTRIBUTED_SERVERS]
ring = HashRing(distrib_servers, {x['id']: x['weight'] for x in settings.DISTRIBUTED_SERVERS})


def is_my_file(filename):
    res = filter(lambda x: x.isdigit(), filename.replace('\\', '/').split('/'))
    if res and len(res) > 1 and len(res[0]) == 3 and len(res[1]) == 10:
        return settings.DISTRIBUTED_SERVER_ID == ring.get_node('/'.join(res))
    return settings.DISTRIBUTED_SERVER_ID == settings.DISTRIBUTED_SERVERS[0]['id']


def get_machine_by_path(filename):
    res = filter(lambda x: x.isdigit(), filename.replace('\\', '/').split('/'))
    serv_id = ring.get_node('/'.join(res))
    return [x['url'] for x in settings.DISTRIBUTED_SERVERS if x['id'] == serv_id][0]


def get_image_path(instance, filename, extra_path=''):
    ext = os.path.splitext(filename)[-1]
    if isinstance(filename, unicode):
        filename = filename.encode('utf8', 'ignore')
    h = md5(filename).hexdigest()[:4]
    t = int(time.time())
    return extra_path + "%s_%s%s" % (h, t, ext)


def _calc_max_width_height(org, max_width, max_height):
    org_x, org_y = (org[0] * 1.0, org[1] * 1.0)
    if org_x / (max_width * 1.0) > org_y / (max_height * 1.0):
        return _calc_max_width(org, max_width)
    else:
        return _calc_max_height(org, max_height)


def _calc_max_width(org, max_width):
    org_x, org_y = (org[0] * 1.0, org[1] * 1.0)
    return (max_width, int(org_y / (org_x / (1.0 * max_width))))


def _calc_max_height(org, max_height):
    org_x, org_y = (org[0] * 1.0, org[1] * 1.0)
    return (int(org_x / (org_y / (1.0 * max_height))), max_height)


def _calc_min_width(org, min_width):
    org_x, org_y = (org[0] * 1.0, org[1] * 1.0)
    return (min_width, int(org_y / (org_x / (1.0 * min_width))))


def _calc_min_height(org, min_height):
    org_x, org_y = (org[0] * 1.0, org[1] * 1.0)
    return (int(org_x / (org_y / (1.0 * min_height))), min_height)


def _calc_min_width_height(org, min_width, min_height):
    org_x, org_y = (org[0] * 1.0, org[1] * 1.0)
    if org_x / (min_width * 1.0) > org_y / (min_height * 1.0):
        return _calc_min_height(org, min_height)
    else:
        return _calc_min_width(org, min_width)


def _calc_size_min(org, min_size):
    org_x, org_y = (org[0] * 1.0, org[1] * 1.0)
    if org_x < org_y:
        return (min_size, int(org_y / (org_x / (1.0 * min_size))))
    else:
        return (int(org_x / (org_y / (1.0 * min_size))), min_size)


def convert_raw_image(img, width=0, height=0, mode=1, enlarge=True, use_storage=None):
    return _get_thumb(img, width=width, height=height, mode=mode, enlarge=enlarge, bin_2_bin=True, use_storage=use_storage)


def convert_obj_image(img, width=0, height=0, mode=1, enlarge=True, use_storage=None):
    return _get_thumb(img, width=width, height=height, mode=mode, enlarge=enlarge, as_img=True, use_storage=use_storage)


def _get_thumb(img, width=0, height=0, mode=1, enlarge=True, bin_2_bin=False, as_img=False, use_storage=None):
    '''
    modes:
    1 - fit to rectangle
    2 - crop
    3 - scale

    '''
    my_storage = use_storage or storage
    name = ''
    if as_img and img:
        pass
    elif isinstance(img, basestring) and not bin_2_bin:
        if not my_storage.exists(img):
            return ''  # TODO: fixme
        myfile = my_storage.open(img)
        name = img
    elif isinstance(img, File):
        myfile = img
        name = img.name
    elif isinstance(img, file):
        myfile = File(img)
        name = myfile.name
    elif hasattr(img, 'read') and hasattr(img, 'seek'):
        myfile = File(img)
        name = getattr(img, 'name', 'fakefile.jpg')
    if not name and not bin_2_bin and not as_img:
        return ''
    if name:
        bname, ext = os.path.splitext(name)
        new_name = 'thumbnails/' + bname.lstrip('/') + ("_%sx%s_%s%s" % (width, height, mode, ext))
        if not bin_2_bin and my_storage.exists(new_name):
            return my_storage.url(new_name)
    im = img if as_img else Image.open(myfile)
    w, h = im.size
    process_file = True
    if not enlarge and (width == 0 or width >= w) and (height == 0 or height >= h):
        process_file = False
        if bin_2_bin:
            myfile.seek(0)
            return myfile.read()
        elif as_img:
            return im
    im_format = im.format
    if height and not width:
        new_w, new_h = _calc_max_height(im.size, height)
    elif width and not height:
        new_w, new_h = _calc_max_width(im.size, width)
    elif width and height:
        if mode == 1:
            new_w, new_h = _calc_max_width_height(im.size, width, height)
        else:
            new_w, new_h = width, height
    else:
        if bin_2_bin:
            myfile.seek(0)
            return myfile.read()
        elif as_img:
            return im
        return my_storage.url(name)

    if mode == 2:
        new_w1, new_h1 = _calc_min_width_height(im.size, width, height)
        offset_w, offset_h = 0, 0
        if new_w1 > new_w:
            offset_w = (new_w1 - new_w) / 2
        else:
            offset_h = (new_h1 - new_h) / 2
        im = im.resize((new_w1, new_h1), Image.ANTIALIAS)
        im = im.crop((offset_w, offset_h, new_w + offset_w, new_h + offset_h))
    else:
        if process_file:
            im = im.resize((new_w, new_h), Image.ANTIALIAS)
    if as_img:
        return im
    fp = StringIO()
    fp.name = new_name
    im.save(fp, format=im_format)
    fp.seek(0)
    if bin_2_bin:
        return fp.read()
    new_name = my_storage.save(new_name, fp)
    return my_storage.url(new_name)

make_thumbnail = _get_thumb

if settings.MONGODB_CFG and settings.MONGODB_CFG.get('ENABLED', True):
    from mongoengine import connect
    for instance in settings.MONGODB_CFG.get('instances', []):
        connect(settings.MONGODB_CFG['instances'][instance]['DB'], alias=instance,
                host=settings.MONGODB_CFG['instances'][instance]['HOST'])


def solr_str_escape(val, plus_spaces=False):
    spc_char = '+' if plus_spaces else ' '
    val = val.replace('\\', r'\\')
    if plus_spaces:
        val = val.replace('+', r'\+')
    val = val.replace(' ', r'\%s' % spc_char)
    for c in ['-', '&', '|', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?', ':']:
        val = val.replace(c, '\\%s' % c)
    return val


class FixMultiDbQset(QuerySet):
    def create(self, *args, **kwargs):
        using = kwargs.pop('_using', None)
        if using:
            with switch_db(self._document, using) as cls:
                return cls(*args, **kwargs).save()
        return super(FixMultiDbQset, self).create(*args, **kwargs)


class MongoSynchronizer(object):
    class_django = None
    class_mongo = None
    field_mapper = {}
    rev_mapper = None
    django_id = 'db_id'
    value_getters = {}
    rev_value_getters = {}
    mongo_special_property_fields = []
    django_special_property_fields = []
    mongo_fields_only = None
    django_fields_only = None
    mongo_unique_val = None

    def __init__(self, using='default'):
        self.using = using

    def _get_val_getter(self, django_f_type):
        if django_f_type == 'DateField':
            return lambda d: datetime.datetime.combine(d, datetime.datetime.min.time()) if d else None
        return (lambda x: x)

    def _get_mongo_val_getter(self, mongo_f_type):
        return (lambda x: x)

    def _prepare_data_for_mongo(self, instance):
        all_fields = {}
        for f in self.class_django._meta.fields:
            if f.name == 'id':
                continue
            mongo_f = self.field_mapper.get(f.name, f.name)
            if not mongo_f or (self.django_fields_only and f.name not in self.django_fields_only):
                continue
            django_f_type = f.__class__.__name__
            all_fields[mongo_f] = self.value_getters.get(mongo_f, self._get_val_getter(django_f_type))(getattr(instance, f.name, None))
        for f in self.django_special_property_fields:
            mongo_f = self.field_mapper.get(f, f)
            all_fields[mongo_f] = getattr(instance, f, None)
        return all_fields

    def _prepare_data_for_django(self, instance):
        all_fields = {}
        fields = [getattr(self.class_mongo, f) for f in dir(self.class_mongo) if isinstance(getattr(self.class_mongo, f), BaseField)]
        for f in fields:
            if f.name == 'id' or f.name == self.django_id or f.name == '_cls':
                continue
            django_f = self._get_django_field(f.name)
            if not django_f or (self.mongo_fields_only and f.name not in self.mongo_fields_only):
                continue
            mongo_f_type = f.__class__.__name__
            all_fields[django_f] = self.rev_value_getters.get(django_f, self._get_mongo_val_getter(mongo_f_type))(getattr(instance, f.name, None))
        for f in self.mongo_special_property_fields:
            django_f = self._get_django_field(f)
            all_fields[django_f] = getattr(instance, f, None)
        return all_fields

    def insert(self, instance):
        all_fields = self._prepare_data_for_mongo(instance)
        if self.django_id:
            all_fields[self.django_id] = instance.id
        if all_fields:
            item = self.class_mongo.objects.using(self.using).create(**all_fields)
            # item.save()
            return item
        return False

    def django_insert(self, instance):
        all_fields = self._prepare_data_for_django(instance)
        if all_fields:
            item = self.class_django._default_manager.create(**all_fields)
            # item.save()
            return item
        return False

    def _prepare_for_update(self, what, instance, only=None, deffer=None):
        if what == 'django':
            all_fields = self._prepare_data_for_django(instance)
        elif what == 'mongo':
            all_fields = self._prepare_data_for_mongo(instance)
        else:
            raise ValueError('"what" should be django or mongo, is: %s' % what)
        deffer = deffer or []
        only = only or []
        if only:
            for k in all_fields.keys():
                if k not in only:
                    all_fields.pop(k)
        for d in deffer:
            all_fields.pop(d, None)
        return all_fields

    def update_mongo(self, instance, only=None, deffer=None):
        all_fields = self._prepare_for_update('mongo', instance, only=only, deffer=deffer)
        if self.django_id:
            obj = self.class_mongo.objects(**{self.django_id: instance.id}).using(self.using)
            if not obj.count() and self.mongo_unique_val:
                django_f = self._get_django_field(self.mongo_unique_val)
                obj = self.class_mongo.objects(**{self.mongo_unique_val: getattr(instance, django_f)})
            obj.update(**all_fields)

    def update_django(self, instance, only=None, deffer=None):
        all_fields = self._prepare_for_update('django', instance, only=only, deffer=deffer)
        if self.django_id and getattr(instance, self.django_id):
            self.class_django.objects.filter(pk=getattr(instance, self.django_id)).update(**all_fields)

    def delete(self, instance_id):
        if self.django_id:
            self.class_mongo.objects(**{self.django_id: instance_id}).using(self.using).delete()

    def get_mongo_obj(self, instance):
        if self.django_id:
            obj = self.class_mongo.objects(**{self.django_id: instance.id}).using(self.using)
            if obj.count() == 1:
                return obj[0]

    def filter(self, **kwargs):
        return self.class_mongo.objects(**kwargs).using(self.using)

    def update_or_create_mongo(self, instance, only=None, deffer=None):
        if self.django_id:
            if not self.filter(**{self.django_id: instance.id}).count() and not self.check_unique_val(instance):
                self.insert(instance)
            else:
                self.update_mongo(instance, only=only, deffer=deffer)

    def _get_django_field(self, mongo_f):
        rev_mapper = self.rev_mapper or dict([(v, k) for k, v in self.field_mapper.items()])
        return rev_mapper.get(mongo_f, mongo_f)

    def check_unique_val(self, instance):
        if not self.mongo_unique_val:
            return False
        django_f = self._get_django_field(self.mongo_unique_val)
        if not self.filter(**{self.mongo_unique_val: getattr(instance, django_f)}).count():
            return False
        return True

    def sync_django_db(self, only=None, deffer=None, only_new=False, except_ids=None):
        except_ids = except_ids or []
        for instance in self.filter().all():
            if self.django_id and (only_new or except_ids):
                db_id = getattr(instance, self.django_id, None)
                if (only_new and db_id) or (except_ids and db_id in except_ids):
                    continue
            self.update_or_create_django(instance, only=only, deffer=deffer)

    def update_or_create_django(self, instance, only=None, deffer=None):
        if self.django_id:
            db_id = getattr(instance, self.django_id, None)
            vals = list(self.class_django._default_manager.filter(pk=db_id)) if db_id else []
            if vals:
                self.update_django(instance, only=only, deffer=deffer)
            else:
                try:
                    self.django_insert(instance)
                except Exception, e:
                    self.insertion_failed(instance, e)

    def insertion_failed(self, instance, e):
        raise e
