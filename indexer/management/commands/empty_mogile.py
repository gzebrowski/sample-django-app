# -*- coding: utf-8 -*-

from django.conf import settings

from optparse import make_option

from pymogile import MogileFSError
from .base import TaskCommand
from django.core.files.storage import get_storage_class


class Command(TaskCommand):
    option_list = TaskCommand.option_list + (
        make_option('--all-images',
                    action='store_true',
                    dest='all_images',
                    default=False,
                    help='delete all images'),
        make_option('-s', '--startpath',
                    dest='startpath',
                    type='string',
                    help='start path'
                    ),
    )

    def _reconect_mogile(self):
        self.global_storage = get_storage_class(settings.GLOBAL_FILE_STORAGE)()

    def list_keys(self, pth):
        return self.global_storage.listfiles(pth)

    def _delete(self, val):
        self.global_storage.delete(val)

    def run_task(self):
        if self.options['startpath'] is None and not self.options['all_images']:
            self.add_log("pathdelete is required! Pls use --pathdelete option")
            return

        myrange = ['%0.3d/' % x for x in range(1000)] if self.options['all_images'] else ['']
        startpath = self.options['startpath'] if not self.options['all_images'] else ''
        self._reconect_mogile()
        for k in myrange:
            while True:
                try:
                    keys = self.try_to_execute(self.list_keys, args=[startpath or k], except_func=self._reconect_mogile)
                except MogileFSError, e:
                    if 'no keys' in unicode(e).lower():
                        break
                if not keys:
                    break
                for val in keys:
                    print val
                    self.try_to_execute(self._delete, args=[val], except_func=self._reconect_mogile)
                    self.item_processed()

    def get_total_items(self):
        myrange = ['%0.3d/' % x for x in range(1000)]
        cnt = 0
        for k in myrange:
            try:
                keys = self.global_storage.listfiles(k)
            except MogileFSError, e:
                if 'no keys' in unicode(e).lower():
                    continue
            cnt += len(keys)
        return cnt

    def init(self):
        self._reconect_mogile()
