# -*- coding: utf-8 -*-

import os
import traceback
from StringIO import StringIO
import cStringIO
from PIL import Image

from django.conf import settings

from optparse import make_option
from .base import TaskCommand
from indexer.models import Log
from product.models import Product
from utils.utils import convert_obj_image, is_my_file

path_join = lambda *p: os.path.join(*p).replace('\\', '/')


class Command(TaskCommand):
    LOG_PROGRESS_STEP = 500

    option_list = TaskCommand.option_list + (
        make_option('--overwrite',
                    action='store_true',
                    dest='overwrite',
                    default=False,
                    help='overwrites all files'),
        make_option('--tolerance',
                    dest='tolerance',
                    type='int',
                    default=0,
                    help='tolerance for floodfill (0-255)'),
        make_option('--max-size',
                    dest='max_size',
                    type='int',
                    default=0,
                    help='max size [in px]'),
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

    def switch_to_transparent(self, src_file, dest_file, tolerance=0, max_size=None):
        content = open(src_file, 'rb').read()
        fp2 = cStringIO.StringIO(content)

        img = Image.open(fp2)
        if not img.size[0] or not img.size[1]:
            raise ValueError('wrong image file')
        if max_size:
            img = convert_obj_image(img, width=max_size, height=max_size, enlarge=False)
            img = img.convert("RGBA")
            output = StringIO()
            img.save(output, "PNG")
            output.seek(0)
            open(dest_file, 'wb').write(output.read())
            src_file = dest_file
        cmd = "%(app)s %(src)s -bordercolor white -border 1x1 -matte -fill none -fuzz %(fuzz)s%% -draw 'matte 0,0 floodfill' -shave 1x1 %(dst)s"
        cmd %= {'app': settings.IMAGEMAGIC_PATH, 'src': src_file, 'dst': dest_file, 'fuzz': tolerance}
        os.system(cmd)

    def process_item(self, prod):
        if not prod.relative_img_path:
            return "missing required values relative_img_path for id=%s" % prod.id
        src_file = path_join(settings.STORAGE_ROOT, prod.relative_img_path)
        dest_file = os.path.splitext(path_join(settings.STORAGE_ROOT, 'transparent', prod.relative_img_path))[0] + '.png'
        dirname = os.path.dirname(dest_file)
        if os.path.isfile(dest_file) and not self.options['overwrite']:
            return True
        if not os.path.isfile(src_file):
            return "missing original file %s for id=%s" % (src_file, prod.id)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        try:
            max_size = self.options['max_size']
            self.switch_to_transparent(src_file, dest_file, self.options['tolerance'], max_size=max_size)
            assert os.path.isfile(dest_file)
        except Exception:
            if not prod.image_proc_error:
                prod.image_proc_error = True
                prod.save()
            return "failed to convert file %s for product (id:%s)\n%s\n\n" % (src_file, prod.id, traceback.format_exc())
        else:
            if prod.image_proc_error:
                prod.image_proc_error = False
                prod.save()
        return True

    def get_qset(self):
        kwargs = {}
        kwargs.update({'marked': True} if self.options['only_marked'] else {})
        kwargs.update({'marked': False} if self.options['only_unmarked'] else {})
        return Product.objects.filter(availability=True, file_avaliable=True,
                                      in_collection__gt=0, **kwargs)

    def process_part(self, rng, step):
        prods = self.get_qset().only(
            'id', 'product_img', 'relative_img_path').order_by('product_id')[
                rng:rng + step]  # product_id is semi-random value, so we won't download image after image from the same server
        for prod in prods:
            if not is_my_file(prod.relative_img_path):
                self.item_processed()
                continue
            res = self.process_item(prod)
            self.item_processed()
            if res is not True:
                self.failed_to_convert += 1
            if isinstance(res, basestring):
                self.log_list.append(res)

    def run_task(self):
        start_val = self.task.items_processed
        for rng in xrange(start_val, self.total_items, self.LOG_PROGRESS_STEP):
            self.process_part(rng, self.LOG_PROGRESS_STEP)

    def get_total_items(self):
        # product_img availability relative_img_path file_avaliable
        return self.get_qset().count()

    def after_finish(self):
        if self.log_list:
            self.add_log("Failed to get %s images:\r\n%s" % (len(self.log_list), '\n'.join(self.log_list)), tp=Log.LOGTYPE_WARNING)

    def init(self):
        self.log_list = []
        self.failed_to_convert = 0
