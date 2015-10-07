# -*- coding: utf-8 -*-

"""solrindexer URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.views.generic.base import RedirectView
from indexer.views import RequestThumbnail

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^collection/', include('collection.urls')),
    url(r'^product-thumbnail', RequestThumbnail.as_view(), name='product_thumbnail'),
    url(r'^product/(?P<path>.*)$', RedirectView.as_view(permanent=False, url="http://www.trotylus.pl/product/%(path)s")),
    url(r'^$', RedirectView.as_view(permanent=False, url="/admin/")),
]
if True:  # settings.DEBUG:
    urlpatterns += [url(r'^%s/(?P<path>.*)$' % settings.UPLOAD_URL.strip('/'), 'django.views.static.serve', {
        'document_root': settings.UPLOAD_ROOT})]
admin.site.site_header = 'Live dashboard'
