# -*- coding: utf-8 -*-

import os
import re
import requests
import traceback
import cStringIO
from PIL import Image

from django.conf import settings

from optparse import make_option
from .base import TaskCommand
from indexer.models import Log
from product.models import Product
from utils.utils import convert_raw_image, is_my_file
from django.core.files.storage import get_storage_class
global_storage = get_storage_class(settings.GLOBAL_FILE_STORAGE)()


class Command(TaskCommand):
    LOG_PROGRESS_STEP = 1500

    option_list = TaskCommand.option_list + (
        make_option('--overwite',
                    action='store_true',
                    dest='overwite',
                    default=False,
                    help='overwrites all files'),
        make_option('--check-all-files',
                    action='store_true',
                    dest='check_all_files',
                    default=False,
                    help='check all files'),
        make_option('--from-country',
                    dest='from_country',
                    type='int',
                    default=0,
                    help='only form coutry: 1:UK, 2:USA'),
        make_option('--from-mogilefs',
                    dest='from_mogilefs',
                    action='store_true',
                    default=False,
                    help='from mogilefs instead of external shops'),
        make_option('--only-marked',
                    dest='only_marked',
                    action='store_true',
                    default=False,
                    help='only marked products'),
        make_option('--only-unmarked',
                    dest='only_unmarked',
                    action='store_true',
                    default=False,
                    help='only unmarked products'),
    )

    def process_item(self, prod):

        def _check_img(content, product=None, reraise=False):
            try:
                fp2 = cStringIO.StringIO(content)
                im = Image.open(fp2)
                size = im.size
                assert size[0] > 40 and size[1] > 40
            except Exception:
                if product:
                    product.image_error = True
                    product.save()
                if reraise:
                    raise
                return False
            else:
                if prod and product.image_error:
                    product.image_error = False
                    product.save()
                return True

        if not prod.relative_img_path or not prod.product_img:
            return "missing required values relative_img_path or product_img for id=%s" % prod.id
        dest = os.path.join(settings.STORAGE_ROOT, prod.relative_img_path)
        dirname = os.path.dirname(dest)
        if os.path.isfile(dest) and not self.options['overwite']:
            if self.options['check_all_files']:
                content = open(dest, 'rb').read()
                return _check_img(content, product=prod)
            return True
        if self.options['from_mogilefs']:
            product_img = global_storage.url(prod.relative_img_path)
        else:
            product_img = prod.product_img
        if product_img.startswith('//'):
            product_img = 'http:' + product_img
        try:
            product_img = self.fix_url(product_img)
            content = requests.get(product_img).content
        except Exception:
            return "failed to load file %s for product (id:%s)" % (product_img, prod.id)
        else:
            if len(content) > 50000:
                fp2 = cStringIO.StringIO(content)
                try:
                    content = convert_raw_image(fp2, width=640, height=640, enlarge=False)
                except Exception, e:
                    print traceback.format_exc()
                    return u"failed to convert file %s for product (id:%s): %s" % (product_img, prod.id, unicode(e))
            elif self.options['check_all_files']:
                try:
                    _check_img(content, product=prod, reraise=True)
                except Exception, e:
                    return u"failed to check file %s for product (id:%s): %s" % (product_img, prod.id, unicode(e))
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            open(dest, 'wb').write(content)
        return True

    def process_part(self, rng, step):
        prods = self.get_qset().only(
            'id', 'product_img', 'relative_img_path', 'image_error',
            'file_avaliable').order_by('product_id')
        if self.options.get('check_all_files'):
            prods = prods[rng:rng + step]
        else:
            prods = prods[self.failed_to_download:self.failed_to_download + step]  # product_id is semi-random value, so we won't download image after image from the same server
        for prod in prods:
            if not is_my_file(prod.relative_img_path):
                self.item_processed()
                continue
            res = self.process_item(prod)
            self.item_processed()
            if res is not True:
                self.failed_to_download += 1
            if isinstance(res, basestring):
                self.log_list.append(res)
            elif res is True:
                prod.file_avaliable = True
                prod.save()

    def run_task(self):
        start_val = self.task.items_processed
        for rng in xrange(start_val, self.total_items, self.LOG_PROGRESS_STEP):
            self.process_part(rng, self.LOG_PROGRESS_STEP)

    def get_qset(self):
        kwargs = {'country': int(self.options['from_country'])} if int(self.options.get('from_country', 0)) else {}
        kwargs.update({'marked': True} if self.options['only_marked'] else {})
        kwargs.update({'marked': False} if self.options['only_unmarked'] else {})
        kwargs.update({'file_avaliable': False} if not self.options.get('check_all_files') else {})
        return Product.objects.filter(availability=True, **kwargs)

    def get_total_items(self):
        return self.get_qset().count()
        # product_img availability relative_img_path file_avaliable

    def after_finish(self):
        if self.log_list:
            self.add_log("Failed to get %s images:\r\n%s" % (len(self.log_list), '\n'.join(self.log_list)), tp=Log.LOGTYPE_WARNING)

    def init(self):
        self.log_list = []
        self.failed_to_download = 0

    def fix_url(self, url):
        """ fixing url in some known cases """
        if ':///' in url:
            url = re.sub(r'^http(s?)://[/]+', r'http\1://', url)
        return url
