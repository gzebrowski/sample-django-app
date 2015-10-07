# -*- coding: utf-8 -*-

from django.views.generic.base import View
from django.http import HttpResponseRedirect
from utils.utils import is_my_file, make_thumbnail
from django.http import Http404


class RequestThumbnail(View):
    def get(self, request, *args, **kwargs):
        path = request.GET.get('path')
        if path and is_my_file(path):
            try:
                filename = make_thumbnail(path, 64, 64)
            except Exception:
                pass
            else:
                return HttpResponseRedirect(filename)
        raise Http404
