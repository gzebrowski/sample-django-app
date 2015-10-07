# -*- coding: utf-8 -*-

import os

from django.conf import settings

from optparse import make_option
from .base import TaskCommand
from indexer.models import Log
from product.models import Product
from utils.utils import is_my_file


class Command(TaskCommand):
    LOG_PROGRESS_STEP = 1500
    option_list = TaskCommand.option_list + (
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
        if not prod.relative_img_path:
            return "missing required value relative_img_path for id=%s" % prod.id
        src_file = os.path.join(settings.STORAGE_ROOT, prod.relative_img_path)
        transp_dest = os.path.join(settings.STORAGE_ROOT, 'transparent', prod.relative_img_path)
        transp_dest = os.path.splitext(os.path.join(settings.STORAGE_ROOT, 'transparent', prod.relative_img_path))[0] + '.png'
        if (os.path.isfile(src_file) and not os.path.isfile(transp_dest)) or (
                os.path.isfile(src_file) and os.path.isfile(transp_dest) and os.path.getsize(transp_dest) < 1000):
            if not prod.image_proc_error:
                prod.image_proc_error = True
                prod.save()
            return False
        elif prod.image_proc_error:
            prod.image_proc_error = False
            prod.save()
        return True

    def process_part(self, rng, step):
        prods = self.get_qset().only(
            'id', 'relative_img_path', 'image_error',
            'image_proc_error', 'file_avaliable').order_by('id')
        prods = prods[rng:rng + step]
        for prod in prods:
            if not is_my_file(prod.relative_img_path):
                self.item_processed()
                continue
            res = self.process_item(prod)
            self.item_processed()
            if res is not True:
                self.wrong_files += 1
            if isinstance(res, basestring):
                self.log_list.append(res)

    def run_task(self):
        for rng in xrange(0, self.total_items, self.LOG_PROGRESS_STEP):
            self.process_part(rng, self.LOG_PROGRESS_STEP)

    def get_qset(self):
        kwargs = {}
        kwargs.update({'marked': True} if self.options['only_marked'] else {})
        kwargs.update({'marked': False} if self.options['only_unmarked'] else {})
        return Product.objects.filter(availability=True, in_collection__gt=0, file_avaliable=True, **kwargs)

    def get_total_items(self):
        return self.get_qset().count()
        # product_img availability relative_img_path file_avaliable

    def after_finish(self):
        if self.log_list:
            self.add_log("Failed to check %s images.\r\n%s" % (len(self.wrong_files), '\n'.join(self.log_list)), tp=Log.LOGTYPE_WARNING)

    def init(self):
        self.log_list = []
        self.wrong_files = 0
