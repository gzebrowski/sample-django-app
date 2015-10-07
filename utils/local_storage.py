# -*- coding: utf-8 -*-

from django.core.files.storage import FileSystemStorage
from django.conf import settings


class MyLocalStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None):
        if location is None:
            location = settings.UPLOAD_ROOT
        if base_url is None:
            base_url = settings.UPLOAD_URL
        super(MyLocalStorage, self).__init__(location=location, base_url=base_url)

    def get_from_url(self, url):
        url = str(url).replace('\\', '/')
        name = ''
        if url.startswith(self.base_url):
            name = url[len(self.base_url):].strip('/')
        return name

    def listdir(self, path, *args, **kwargs):
        try:
            return super(MyLocalStorage, self).listdir(path, *args, **kwargs)
        except OSError:
            return [], []
