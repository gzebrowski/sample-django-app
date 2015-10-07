# -*- coding: utf-8 -*-

import os

from django.conf import settings
from .base import TaskCommand
from django.core.files.storage import get_storage_class
from pymogile import MogileFSError


class Command(TaskCommand):

    def get_iterator_by_key(self, key):
        if key in ('userscollections/', 'collection2/compositions/') and hasattr(self.global_storage, 'listfiles_startswith'):
            for x in range(256):
                h = "%0.2x" % x
                try:
                    keys2 = self.global_storage.listfiles_startswith("%s%s" % (key, h))
                    for k in keys2:
                        yield k
                except MogileFSError:
                    continue
        else:
            keys = self.global_storage.listfiles(key)
            for k in keys:
                yield k

    def run_task(self):
        for d2p in self.dirs_to_process:
            for k in self.get_iterator_by_key(d2p):
                content = self.global_storage.open(k).read()
                filename = os.path.join(self.storage_root, k)
                dir = os.path.dirname(filename)
                if not os.path.isdir(dir):
                    os.makedirs(dir)
                open(os.path.join(self.storage_root, k), 'wb').write(content)
                self.item_processed()

    def get_total_items(self):
        cnt = 0
        for d2p in self.dirs_to_process:
            for k in self.get_iterator_by_key(d2p):
                cnt += 1
        return cnt

    def init(self):
        self.storage_root = settings.STORAGE_ROOT.rstrip('/') + '/'
        self.dirs_to_process = ['collection2/compositions/', 'user-profiles/avatar/', 'userscollections/']
        self._reconect_mogile()

    def _reconect_mogile(self):
        self.global_storage = get_storage_class(settings.GLOBAL_FILE_STORAGE)()
