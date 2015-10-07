# -*- coding: utf-8 -*-

import os
# import traceback
from StringIO import StringIO
import cStringIO
from PIL import Image

from django.conf import settings

from optparse import make_option
from .base import TaskCommand
from indexer.models import Log
from product.models import Product
from utils.utils import convert_obj_image

path_join = lambda *p: os.path.join(*p).replace('\\', '/')


class ImageMatrix(object):
    def __init__(self, data, width, height):
        self.data = list(data)
        self.width = width
        self.height = height
        self.new_data = []
        self.all_keys = []
        self.is_dirty = False

    def raw_get(self, posx, posy):
        return self.data[posx * self.width + posy]

    def get(self, posx, posy):
        assert posx < self.width and posy < self.height
        key = posx * self.width + posy
        if key in self.all_keys:
            return filter(lambda x: x[0] == key, self.new_data)[0][1]
        return self.data[posx * self.width + posy]

    def raw_set(self, posx, posy, val):
        self.new_data.append((posx * self.width + posy, val))

    def set(self, posx, posy, val):
        assert posx < self.width and posy < self.height
        self.is_dirty = True
        key = posx * self.width + posy
        if key in self.all_keys:
            self.new_data = [v for v in self.new_data if v[0] != key]
        else:
            self.all_keys.append(key)
        self.new_data.append((key, val))

    def _unique(self):
        self.new_data.reverse()
        all_keys = []
        new_data = []
        for d in self.new_data:
            if d[0] not in all_keys:
                all_keys.append(d[0])
                new_data.append(d)
        self.new_data = new_data

    def _normalise(self):
        self._unique()
        self.new_data.sort(key=lambda x: x[0])

    def within(self, x, y):
        return x >= 0 and y >= 0 and x < self.width and y < self.height

    def dump(self):
        if not self.is_dirty:
            return self.data
        self._normalise()
        res_data = []
        curr_idx = 0
        for v in self.new_data:
            dt_idx = v[0]
            if dt_idx > curr_idx:
                for tmp in xrange(curr_idx, dt_idx):
                    res_data.append(self.data[tmp])
                curr_idx = dt_idx + 1
            else:
                curr_idx += 1
            res_data.append(v[1])
        for tmp in xrange(curr_idx, self.width * self.height):
            res_data.append(self.data[tmp])
        self.is_dirty = False
        self.data = res_data
        self.all_keys = []
        self.new_data = []
        return res_data


class Command(TaskCommand):
    LOG_PROGRESS_STEP = 20

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
    )

    def flood_fill(self, image, x, y, value, tolerance=0, temp_val='x'):
        "Flood fill on a region of non-BORDER_COLOR pixels."
        p0 = image.get(x, y)
        min_1, max_1 = max(0, p0[0] - tolerance), min(255, p0[0] + tolerance)
        min_2, max_2 = max(0, p0[1] - tolerance), min(255, p0[1] + tolerance)
        min_3, max_3 = max(0, p0[2] - tolerance), min(255, p0[2] + tolerance)
        in_tolerance = lambda pix: pix[0] >= min_1 and pix[0] <= max_1 and \
            pix[1] >= min_2 and pix[1] <= max_2 and pix[2] >= min_3 and pix[2] <= max_3
        if not image.within(x, y) or not in_tolerance(image.get(x, y)):
            return image.dump()
        edge = [(x, y)]
        image.set(x, y, temp_val)
        used = []
        while edge:
            newedge = []
            for (x, y) in edge:
                for (s, t) in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if (s, t) not in used and s >= 0 and t >= 0 and s < image.height and t < image.width:
                        curr_val = image.raw_get(s, t)
                        if curr_val != temp_val and in_tolerance(curr_val):
                            image.raw_set(s, t, temp_val)
                            newedge.append((s, t))
                        used.append((s, t))
            edge = newedge
        data = image.dump()
        return [(value if x == temp_val else x) for x in data]

    def shitch_to_transparent(self, img, tolerance=0, max_size=None):
        img = Image.open(img)
        if max_size:
            img = convert_obj_image(img, width=max_size, height=max_size, enlarge=False)
        img = img.convert("RGBA")
        if not img.size[0] or not img.size[1]:
            return img
        datas = ImageMatrix(img.getdata(), *img.size)
        newData = self.flood_fill(datas, 0, 0, (255, 255, 255, 0), tolerance=tolerance)
        '''
        corner_point = datas.get(0, 0)
        newData = []
        for item in datas:
            if item[0] == 255 and item[1] == 255 and item[2] == 255:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)
        '''
        output = StringIO()
        img.putdata(newData)
        img.save(output, "PNG")
        output.seek(0)
        return output.read()

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
        content = open(src_file, 'rb').read()
        fp2 = cStringIO.StringIO(content)
        try:
            max_size = self.options['max_size']
            new_img = self.shitch_to_transparent(fp2, self.options['tolerance'], max_size=max_size)
        except Exception:
            return "failed to convert file %s for product (id:%s)\n" % (src_file, prod.id)
        else:
            open(dest_file, 'wb').write(new_img)
        return True

    def process_part(self, rng, step):
        prods = Product.objects.filter(
            availability=True, file_avaliable=True, in_collection__gt=0).only(
                'id', 'product_img', 'relative_img_path').order_by('product_id')[
                    rng:rng + step]  # product_id is semi-random value, so we won't download image after image from the same server
        for prod in prods:
            res = self.process_item(prod)
            self.item_processed()
            if res is not True:
                self.failed_to_convert += 1
            if isinstance(res, basestring):
                self.log_list.append(res)

    def run_task(self):
        for rng in xrange(0, self.total_items, self.LOG_PROGRESS_STEP):
            self.process_part(rng, self.LOG_PROGRESS_STEP)

    def get_total_items(self):
        # product_img availability relative_img_path file_avaliable
        return Product.objects.filter(availability=True, file_avaliable=True, in_collection__gt=0).count()

    def after_finish(self):
        if self.log_list:
            self.add_log("Failed to get %s images:\r\n%s" % (len(self.log_list), '\n'.join(self.log_list)), tp=Log.LOGTYPE_WARNING)

    def init(self):
        self.log_list = []
        self.failed_to_convert = 0
