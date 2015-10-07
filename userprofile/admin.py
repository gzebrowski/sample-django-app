# -*- coding: utf-8 -*-

import datetime
from django.contrib import admin

from .models import ProfileUser
from django.contrib.auth.admin import UserAdmin

from mongo_models import User as MongoSiteUser
from utils.utils import MongoSynchronizer
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect


class UserSynchronizer(MongoSynchronizer):
    class_django = ProfileUser
    class_mongo = MongoSiteUser
    value_getters = {'logo_image': lambda i: getattr(i, 'url', str(i or ''))}
    rev_value_getters = {'end_date': lambda d: d.date() if isinstance(d, datetime.datetime) else d}
    field_mapper = {'date_joined': 'created_at', 'full_name': 'name', 'is_active': 'user_is_active'}
    mongo_special_property_fields = ['social_user', 'social_user_data', 'username']
    django_fields_only = ['date_joined', 'full_name', 'email', 'gender', 'confirmed', 'is_active', 'is_staff', 'is_superuser']
    rev_mapper = None
    mongo_unique_val = 'email'

    def insertion_failed(self, instance, e):
        pass


class MyUserAdmin(UserAdmin):
    list_display = ['id', 'username', 'email', 'full_name', 'gender', 'is_staff', 'is_superuser']
    fieldsets = UserAdmin.fieldsets + (('Additional', {'fields': ('full_name', 'gender')}),)
    list_filter = UserAdmin.list_filter + ('gender',)
    actions = ['put_selected_to_mongo', 'update_users', 'delete_offers']

    def get_actions(self, *args, **kwargs):
        result = super(MyUserAdmin, self).get_actions(*args, **kwargs)
        if 'delete_selected' in result:
            result.pop('delete_selected')
        return result

    def put_selected_to_mongo(self, request, queryset):
        synchr = UserSynchronizer('default')
        for instance in queryset:
            synchr.update_or_create_mongo(instance)

    def update_users(self, request, queryset):
        synchr = UserSynchronizer('default')
        pks = queryset.objects.all().values_list('pk', flat=True)
        synchr.sync_django_db(except_ids=pks)

    def get_new_users(self, request, *args, **kwargs):
        synchr = UserSynchronizer('default')
        synchr.sync_django_db(only_new=True)
        self.message_user(request, 'New users were imported', messages.INFO)
        return HttpResponseRedirect(reverse('admin:userprofile_profileuser_changelist'))

    def delete_model(self, request, obj):
        synchr = UserSynchronizer('default')
        synchr.delete(obj.id)
        obj.delete()

    def get_urls(self):
        from django.conf.urls import patterns, url
        orgpatterns = super(MyUserAdmin, self).get_urls()
        urlpatterns = patterns(
            '', url(r'^get-new-users/$',
                    self.get_new_users,
                    name='get_new_users'))
        return urlpatterns + orgpatterns

admin.site.register(ProfileUser, MyUserAdmin)
