# -*- coding: utf-8 -*-

import datetime
from django.contrib import admin
from django import forms
from django.contrib.admin import helpers
from django.contrib import messages
from .models import SpecialOffer, ExtraClass, global_storage

from mongo_models import SpecialOffer as MongoSpecialOffer
from utils.utils import MongoSynchronizer, make_thumbnail
from django.conf import settings


class SpecialOfferSynchronizer(MongoSynchronizer):
    class_django = SpecialOffer
    class_mongo = MongoSpecialOffer
    value_getters = {'logo_image': lambda i: getattr(i, 'url', str(i or '')),
                     'extra_class': lambda i: i.key if i else None}
    rev_value_getters = {'end_date': lambda d: d.date() if isinstance(d, datetime.datetime) else d}


class ExtraActionFormMixIn(object):

    def __init__(self, *args, **kwargs):
        super(ExtraActionFormMixIn, self).__init__(*args, **kwargs)
        self.fields['db_instance'].choices = (('', '-- not needed --'),) + settings.ALL_DB_INSTANCES


class ExtraActionForm(ExtraActionFormMixIn, forms.Form):
    db_instance = forms.ChoiceField(required=False, choices=[])


class MyActionForm(ExtraActionFormMixIn, helpers.ActionForm):
    db_instance = forms.ChoiceField(required=False, choices=[])


@admin.register(SpecialOffer)
class SpecialOfferAdmin(admin.ModelAdmin):
    action_form = MyActionForm
    list_display = ['id', 'logo', 'title', 'end_date', 'box_size', 'popularity', 'country', 'is_freeshiping', 'is_discount']
    list_filter = ['box_size', 'country', 'is_freeshiping', 'is_discount']
    actions = ['put_selected_to_mongo', 'update_popularity', 'delete_offers']

    def logo(self, obj):
        if obj.logo_image:
            try:
                filename = make_thumbnail(obj.logo_image, 0, 0, use_storage=global_storage)
            except Exception:
                return ''
            return '<img alt="" width="64" src="%s" />' % (filename,)
        return ''
    logo.allow_tags = True

    def get_actions(self, *args, **kwargs):
        result = super(SpecialOfferAdmin, self).get_actions(*args, **kwargs)
        if 'delete_selected' in result:
            result.pop('delete_selected')
        return result

    def put_selected_to_mongo(self, request, queryset):
        ex_form = ExtraActionForm(request.POST)
        if ex_form.is_valid() and ex_form.cleaned_data.get('db_instance'):
            synchr = SpecialOfferSynchronizer(ex_form.cleaned_data['db_instance'])
            for instance in queryset:
                synchr.update_or_create_mongo(instance, deffer=['popularity'])

    def update_popularity(self, request, queryset):
        ex_form = ExtraActionForm(request.POST)
        if ex_form.is_valid() and ex_form.cleaned_data.get('db_instance'):
            synchr = SpecialOfferSynchronizer(ex_form.cleaned_data['db_instance'])
            for instance in queryset:
                instance2 = synchr.get_mongo_obj(instance)
                synchr.update_django(instance2, only=['popularity'])

    def delete_model(self, request, obj):
        for k in dict(settings.ALL_DB_INSTANCES).keys():
            synchr = SpecialOfferSynchronizer(k)
            synchr.delete(obj.id)
        obj.delete()
        ex_form = ExtraActionForm(request.POST)
        if ex_form.is_valid() and ex_form.cleaned_data.get('db_instance'):
            self.message_user(request, 'The db instance was ignored - performed acction for all instances', messages.WARNING)

    def delete_offers(self, request, queryset):
        for instance in queryset:
            self.delete_model(request, instance)


@admin.register(ExtraClass)
class ExtraClassAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'key', 'description']
