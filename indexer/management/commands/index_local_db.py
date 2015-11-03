# -*- coding: utf-8 -*-

import datetime
import os
import re
import time
import urlparse
from hashlib import md5

from django.conf import settings

from .base import TaskCommand
from pymongo import MongoClient
from indexer.models import Log, WorkingTask
from product.models import Brand, Shop, MainCategory, Product, RemovedItems
from django.template.defaultfilters import slugify
from utils.utils import TimeDebuger
from category.models import Category
from treebeard.exceptions import PathOverflow


class Helper(object):
    def _strip(self, val):
        return unicode(val or '').strip()

    def _lc(self, val):
        return self._strip(val).lower()

    def _up(self, val):
        return self._strip(val).upper()


class Command(TaskCommand, Helper):
    def process_item(self, p):
        def _row_str(row2):
            return (row2.get(u'product_id', '-- missing product_id --'), row2.get(u'original_url', u'-- missing original url --'))
        row = {'source': self.task.mongodb_instance}
        fields_to_normalize = [u'product_name', u'product_description',
                               u'source_text', u'product_brand',
                               u'product_category', u'product_colors',
                               u'original_url', u'product_img', u'size',
                               u'product_sub_category']
        for f in fields_to_normalize:
            val = p.get(f)
            if not val or not isinstance(val, basestring):
                continue
            if isinstance(val, str):
                val = val.decode('utf8', errors="replace")
                val = val.replace(u'\ufffd', ' ').strip()
            val = val.encode('utf8', errors="ignore")
            val = val.replace('\xc2', '').replace('\xc3', '').replace('\xe2', '')
            val = val.decode('utf8', errors="replace").replace(u'\ufffd', ' ').strip()
            p[f] = val
        extra_filter_fields = [u'source_text', u'product_brand', u'product_category',
                               u'product_colors', u'product_sub_category']
        for f in extra_filter_fields:
            val = p.get(f)
            if not val or not isinstance(val, basestring):
                continue
            val = re.sub(ur"[^a-zA-Z0-9@&'©®,. -]", u' ', val).strip()
            val = re.sub(ur'[ ]{2,}', ' ', val)
            p[f] = val
        shop_name = self._up(p.get(u'source_text'))
        if shop_name not in self.all_shops:
            try:
                s, _ = Shop.objects.get_or_create(name=shop_name)
            except Exception, e:
                return str(e)
            else:
                self.all_shops[shop_name] = s.pk
        row['shop_id'] = self.all_shops[shop_name] if shop_name else None
        brand_name = self._up(p.get(u'product_brand'))
        if brand_name not in self.all_brands:
            try:
                s, _ = Brand.objects.get_or_create(name=brand_name)
            except Exception, e:
                return str(e)
            else:
                self.all_brands[brand_name] = s.pk
        row['brand_id'] = self.all_brands[brand_name] if brand_name else None
        country_map = {'united kingdom': 1, 'uk': 1, 'us': 2, 'usa': 2, 'united states': 2}
        row['country'] = country_map.get(p.get(u'country', '').lower())
        for r in [u'price_max', u'price', u'original_price', u'original_price_max']:
            try:
                prc = re.sub(r'[^0-9.,]+', '', p.get(r, ''))
                # sometimes price can look like: "1,234.00", or "1234,45", or "1234.56" or "1,234"
                if '.' not in prc and ',' in prc and not re.search(',[0-9]{3}', prc):
                    prc = prc.replace(',', '.')
                row[r] = float(prc.replace(',', ''))
            except Exception:
                pass
        if row.get('price') and row.get('original_price') and row['price'] >= (row['original_price'] - 0.1):
            if row.get('original_price_max') and row.get('price_max') and row['original_price_max'] > row['price_max']:
                pass
            else:
                row.pop('original_price', None)
                row.pop('original_price_max', None)
        for r in [u'product_name', u'product_description', u'product_img', u'size']:
            row[r] = self._strip(p.get(r))
        for r in [u'product_category', u'product_colors', u'product_sub_category']:
            row[r] = self._up(p[r]) if p.get(r) else None
        for mongo_row, dbrow in ((u'id', 'original_url'), (u'_id', 'external_db_id')):
            row[dbrow] = self._strip(p.get(mongo_row))
        main_categories = [x.strip().upper() for x in p.get(u'main_category').split(',')]
        main_categories_map = {'ACCESSORY': 'ACCESSORIES'}
        main_categories = set([main_categories_map.get(c, c) for c in main_categories])
        main_categories = main_categories.intersection(set(self.cats.keys()))
        main_categories_keys = sorted(list(main_categories))
        one_main_category = main_categories_keys[-1] if main_categories_keys else ''
        main_categories = [self.cats.get(c) for c in main_categories]
        aval_dict = {'0': False, 'false': False, 'no': False}
        availability = unicode(p.get('availability', 'true')).lower()
        row['availability'] = aval_dict.get(availability, True)
        if not row['availability']:
            return True
        try:
            row['crawl_date'] = datetime.datetime.strptime(p[u'crawl_date'], '%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
        row['product_id'] = int(str(int(md5(row.get('original_url', u'').encode('utf8')).hexdigest(), 16))[-10:])
        # {u'price_max': u'360.00', u'crawl_date': u'2014-12-19 10:34:31', u'product_id': u'51899827', u'main_category': u'WOMEN,ACCESSORY,SALES', u'product_category': u'WOMEN', u'country': u'United Kingdom', u'product_colors': None, u'availability': u'true', u'product_description': u'Luxuriously cosy thanks to its large size and super soft finish, this is the statement scarf you need this autumn/winter. In a bold black and white dogtooth complete with a softly fringed edge, this scarf looks stylish worn looped around in the typical fashion, or draped across your shoulders in place of a jacket.', u'id': u'http://www.austinreed.co.uk/fcp/product/austinreed/Hats,-Gloves-and-Scarves/Black-and-White-Large-Dogtooth-Scarf/16428', u'price': u'57.50', u'product_brand': u'AUSTINREED', u'source_text': u'austinreed_uk', u'_id': ObjectId('54a0f2450cf26817f7f714b3'), u'product_name': u'Black and White Large Dogtooth Scarf', u'product_img': u'http://media.austinreed.net/pws/images/catalogue/products/0380615185/large/0380615185_1.jpg', u'size': None}
        if not main_categories:
            return "missing main category for product: (%s/%s)" % _row_str(row)
        missing_fields = []
        for req_field in ['country', 'brand_id', 'shop_id', 'price', 'product_name', 'product_img', 'original_url']:
            if not row.get(req_field):
                missing_fields.append(req_field)
        if missing_fields:
            return "missing required fields (%s) for product: (%s/%s)" % ((', '.join(missing_fields),) + _row_str(row))
        data_hash = md5(unicode([(k, unicode(row[k])) for k in sorted(row.keys())] + main_categories_keys)).hexdigest()
        row['data_hash'] = data_hash
        original_url_hash = md5(row['original_url']).hexdigest()
        if row['data_hash'] in self.all_hashes:
            self.all_hashes.discard(row['data_hash'])
            return True
        if original_url_hash in self.blocked_hashes:
            self.blocked_hashes.discard(original_url_hash)
            return True
        try:
            parsed = urlparse.urlparse(row['product_img'])
            ext = os.path.splitext(parsed.path)[-1]
            fname = slugify(row['product_name'])[:64]
            val = "%0.10d" % row['product_id']
        except Exception:
            return "couldn't prepare image path for product: (%s/%s)" % _row_str(row)
        else:
            row['relative_img_path'] = '%s/%s/%s%s' % (val[:3], val, fname, ext)
        original_url = '--- missing original_url ---'
        row['category_id'] = self.get_cat_id(row, main_category=one_main_category)
        product_sub_category = row.pop('product_sub_category', '')
        row['product_category'] = '|'.join([one_main_category, row['product_category'],
                                           product_sub_category])[:128]
        try:
            original_url = row.pop('original_url')
            p, created = Product.objects.get_or_create(
                original_url=original_url, defaults=row)
            if not created:
                for kk in row:
                    setattr(p, kk, row[kk])
                p.save()
        except Exception, e:
            return str(e) + ', id:' + original_url
        else:
            p.main_category.add(*main_categories)
        return True

    def get_cat_id(self, row, main_category=None):
        product_category = row.get('product_category')
        product_sub_category = row.get('product_sub_category')
        ks = [main_category, product_category, product_sub_category]
        k2 = []
        for k in ks:
            if not k:
                break
            k2.append(k)
        key = tuple(map(slugify, k2))
        if key in self.category_ids:
            return self.category_ids[key]
        query_kwargs = {}
        cat = None
        for nr, val in enumerate(zip(k2, key)):
            name, slug = val
            try:
                cat = Category.objects.get(name=name,
                                           depth=nr + 1, **query_kwargs)
            except Category.DoesNotExist:
                h = cat.add_child if cat else Category.add_root
                try:
                    cat = h(name=name, slug=slug)
                except PathOverflow:
                    raise  # TODO
                self.category_ids[tuple(key[:nr + 1])] = cat.id
            query_kwargs = {'path__startswith': cat.path}
        return cat.id if cat else None

    def run_task(self):
        step = 10000
        reconect_by = step * 5
        start_val = self.task.items_processed
        if self.total_items:
            for start in xrange(start_val, self.total_items, step):
                if start % (int(reconect_by / step) * step) == 0:
                    self._reconect()
                for try_no in range(4, -1, -1):
                    current_set = []
                    try:
                        for p in self.collection.find().skip(start).limit(step):
                            current_set.append(dict(p))
                    except Exception:
                        if not try_no:
                            raise
                        time.sleep(7)
                        self._reconect()
                        continue
                    else:
                        for p in current_set:
                            res = self.process_item(p)
                            self.item_processed()
                            if isinstance(res, basestring):
                                self.log_list.append(res)
                            if len(self.log_list) > 1000:
                                self.save_log_list()
                        break

    def save_log_list(self):
        self.used_fs_logs += len(self.log_list)
        open(os.path.join(settings.TASKLOGS_DIR, 'task_%s.log' % self.task.id), 'a').write('\r\n'.join(self.log_list))
        del self.log_list
        self.log_list = []

    def get_total_items(self):
        if not self.task.mongodb_instance:
            return 0
        return self.collection.count()

    def after_finish(self):
        if self.used_fs_logs:
            self.save_log_list()
            self.add_log("Failed to copy %s records. See the %s." % (self.used_fs_logs, os.path.join(settings.TASKLOGS_DIR, 'task_%s.log' % self.task.id)))
        elif self.log_list:
            self.add_log("Failed to copy %s records:\r\n%s" % (len(self.log_list), '\n'.join(self.log_list)), tp=Log.LOGTYPE_WARNING)
        if self.task.status == WorkingTask.STATUS_FINISHED:
            all_hashes = list(self.all_hashes)
            outdate_time = datetime.datetime.now()
            for x in xrange(0, len(all_hashes), 500):
                Product.objects.filter(source=self.task.mongodb_instance, data_hash__in=all_hashes[x:x + 500]).update(
                    availability=False, outdated=outdate_time)
        tm_debug = self.time_debuger.dump()
        tm_debug and self.add_log(tm_debug)

    def _reconect(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        if self.task.mongodb_instance:
            self.client = MongoClient(self.task.mongodb_instance.host, int(self.task.mongodb_instance.port))
            self.db = self.client[self.task.mongodb_instance.db]
            self.collection = getattr(self.db, self.task.mongodb_instance.collection)

    def init(self):
        self.all_hashes = set(list(Product.objects.filter(availability=True).values_list('data_hash', flat=True)))
        self.blocked_hashes = set(list(RemovedItems.objects.all().values_list('original_url_hash', flat=True)))
        self.client = None
        self.all_shops = {}
        self.all_brands = {}
        self.log_list = []
        self.used_fs_logs = 0
        self.time_debuger = TimeDebuger()
        _cats = list(MainCategory.objects.all())
        self.cats = dict([(c.name, c) for c in _cats])
        self.category_ids = Category.get_categories_as_keys()
        self._reconect()
