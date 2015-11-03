# -*- coding: utf-8 -*-

from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import MoveNodeForm
from .models import Category
from .mongo_models import Category as MongoCategory
from utils.utils import MongoSynchronizer


class CategorySynchronizer(MongoSynchronizer):
    class_django = Category
    class_mongo = MongoCategory


class CategoryForm(MoveNodeForm):
    class Meta:
        model = Category
        exclude = ['path', 'depth', 'numchild']


@admin.register(Category)
class CategoryAdmin(TreeAdmin):
    list_display = ['id', 'name', 'active']
    prepopulated_fields = {"slug": ("name",)}
    form = CategoryForm
    actions = ['put_selected_to_mongo', 'delete_categories', 'synchronize_mongo']

    def get_actions(self, *args, **kwargs):
        result = super(CategoryAdmin, self).get_actions(*args, **kwargs)
        if 'delete_selected' in result:
            result.pop('delete_selected')
        return result

    def put_selected_to_mongo(self, request, queryset):
        synchr = CategorySynchronizer('default')
        for instance in queryset:
            synchr.update_or_create_mongo(instance)

    def synchronize_mongo(self, request, queryset):
        synchr = CategorySynchronizer('default')
        synchr.empty_mongo()
        self.put_selected_to_mongo(request, queryset)

    def delete_model(self, request, obj):
        synchr = CategorySynchronizer('default')
        synchr.delete(obj.id)
        obj.delete()

    def delete_categories(self, request, queryset):
        for instance in queryset:
            self.delete_model(request, instance)
