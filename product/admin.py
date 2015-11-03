# -*- coding: utf-8 -*-

import datetime
import urllib2
import solr
from hashlib import md5
# from collections import OrderedDict
from django.contrib import admin
from django import forms
from django.db.models import F
from django.core.urlresolvers import reverse
from django.contrib.admin import helpers
from category.models import Category
from .models import Brand, Shop, MainCategory, Product, ProductTag, RemovedItems
from utils.utils import make_thumbnail
from utils.utils import is_my_file, get_machine_by_path
from django.contrib import messages


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['id', 'name', 'show_products']

    def show_products(self, obj):
        url = '<a href="%s?brand=%s">list</a>' % (reverse('admin:product_product_changelist'), obj.id)
        return url
    show_products.allow_tags = True


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ['id', 'name', 'show_products']

    def show_products(self, obj):
        url = '<a href="%s?shop=%s">list</a>' % (reverse('admin:product_product_changelist'), obj.id)
        return url
    show_products.allow_tags = True


@admin.register(MainCategory)
class MainCategoryAdmin(admin.ModelAdmin):
    pass


class IsSaleListFilter(admin.SimpleListFilter):
    title = 'Is sale'
    parameter_name = 'issale'

    def lookups(self, request, model_admin):
        return ((1, 'Yes'),)

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(original_price__isnull=False).filter(original_price__gt=F('price'))
        return queryset


class InCollectionFilter(admin.SimpleListFilter):
    title = 'In collection'
    parameter_name = 'incoll'

    def lookups(self, request, model_admin):
        return (('yes', 'Yes'),) + Product._meta.get_field_by_name('in_collection')[0].choices

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == 'yes':
                return queryset.exclude(in_collection=0)
            return queryset.filter(in_collection=self.value())
        return queryset


class PriceListFilter(admin.SimpleListFilter):
    title = 'Price'
    parameter_name = 'price_between'

    def lookups(self, request, model_admin):
        result = []
        mn, mx = map(float, self.value().split('-')) if self.value() else (None, None)
        for x in range(5):
            start_val, end_val = 10 ** x, 10 ** (x + 1)
            price = "%s-%s" % (start_val, end_val)
            result.append((price, "price %s" % price))
            if mn is not None and mn >= start_val and mx <= end_val:
                for add in [0.3, 0.6, 0.9]:
                    price = "%0.2f-%0.2f" % (10 ** (x + add - 0.3), 10 ** (x + add))
                    result.append((price, "-- price %s" % price))
        return tuple(result)

    def queryset(self, request, queryset):
        if self.value():
            mn, mx = map(float, self.value().split('-'))
            return queryset.filter(price__gte=mn, price__lte=mx)
        return queryset


class CategoryListFilter(admin.SimpleListFilter):
    title = 'Hierarchy Category'
    parameter_name = 'cat'

    def lookups(self, request, model_admin):
        cats = Category.objects.all()
        return [(c.path, c.__unicode__()) for c in cats]

    def queryset(self, request, queryset):
        if self.value():
            cats = list(Category.objects.filter(
                path__startswith=self.value()).values_list('id', flat=True))
            return queryset.filter(category__in=cats)
        return queryset


class ExtraActionFormMixIn(object):

    def __init__(self, *args, **kwargs):
        from indexer.models import SolrInstances
        super(ExtraActionFormMixIn, self).__init__(*args, **kwargs)
        self.fields['solr_instances'].choices = [('', '-- not needed --')] + list(SolrInstances.objects.all().values_list('str_connection', 'name'))


class ExtraActionForm(ExtraActionFormMixIn, forms.Form):
    solr_instances = forms.ChoiceField(required=False, choices=[])


class CategoryFormMixIn(object):
    def __init__(self, *args, **kwargs):
        super(CategoryFormMixIn, self).__init__(*args, **kwargs)
        all_cats = Category.objects.all()
        self.fields['category'].choices = [('', '-- not needed --'), ('-1', 'XXX remove category --')] + [(c.id, unicode(c)) for c in all_cats]


class MyActionForm(ExtraActionFormMixIn, CategoryFormMixIn, helpers.ActionForm):
    solr_instances = forms.ChoiceField(required=False, choices=[])
    category = forms.ChoiceField(required=False, choices=[])


class ExtraCategoryForm(CategoryFormMixIn, forms.Form):
    category = forms.ChoiceField(required=True, choices=[])


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    action_form = MyActionForm
    list_display = ['id', 'thumbnail', 'product_name_url', 'shop_name', 'brand_name', 'country', 'price', 'file_avaliable', 'availability', 'in_collection', 'marked', 'item_errors']
    # list_filter = ('country', 'main_category', 'source', 'file_avaliable', 'availability',
    #               'in_collection', IsSaleListFilter, PriceListFilter, CategoryListFilter)
    list_filter = ('country', 'availability', 'file_avaliable', InCollectionFilter,
                   'image_error', 'image_proc_error', 'data_error', 'marked',
                   PriceListFilter, IsSaleListFilter, CategoryListFilter)
    # date_hierarchy = 'crawl_date'
    search_fields = ['product_name', 'product_category', '=product_id', 'original_url']
    raw_id_fields = ['brand', 'shop']
    readonly_fields = ['external_db_id', 'crawl_date', 'outdated']
    actions = ['make_avaliable', 'make_unavaliable', 'make_file_unavaliable',
               'make_file_avaliable', 'add_to_collection1', 'add_to_collection2',
               'add_to_collection3', 'remove_from_collection', 'update_search_index',
               'mark_products', 'unmark_products', 'remove_and_block',
               'add_to_selected_category']

    def item_errors(self, obj):
        result = [x[0] for x in (('image', obj.image_error), ('data', obj.data_error), ('proc', obj.image_proc_error)) if x[1]]
        return '<br />'.join(result)
    item_errors.allow_tags = True

    def get_actions(self, request):
        actions = super(ProductAdmin, self).get_actions(request)
        # all_cats = Category.objects.all()
        # actions.update(OrderedDict(('add_to_cat_%s' % g.id, (self.__class__.join_to_cat, 'add_to_cat_%s' % g.id, "Add to category: %s" % g.__unicode__())) for g in all_cats))
        return actions

    def shop_name(self, obj):
        return obj.shop.name

    def brand_name(self, obj):
        return obj.brand.name

    def is_sale(self, obj):
        return bool(obj.original_price and obj.price and obj.price < obj.original_price)
    is_sale.boolean = True

    def thumbnail(self, obj):
        if obj.relative_img_path:
            if is_my_file(obj.relative_img_path):
                try:
                    filename = make_thumbnail(obj.relative_img_path, 64, 64)
                except Exception:
                    return ''
            else:
                filename = self.request_remote_thumbnail(obj.relative_img_path)
            return '<img alt="" src="%s" />' % (filename,)
        return ''
    thumbnail.allow_tags = True

    def request_remote_thumbnail(self, path):
        url_rem = get_machine_by_path(path)
        return url_rem + reverse('product_thumbnail') + '?path=' + urllib2.quote(path)

    def product_name_url(self, obj):
        return '<strong>%s</strong><br />%s <a target="_blank" href="%s">-&gt;</a>' % (
            self._categories_as_keys.get(obj.category_id),
            obj.product_name, obj.original_url)
    product_name_url.allow_tags = True
    product_name_url.short_description = 'product name'

    def make_unavaliable(self, request, queryset):
        queryset.update(availability=False, outdated=datetime.datetime.now())
    make_unavaliable.short_description = "make unavaliable"

    def make_avaliable(self, request, queryset):
        queryset.update(availability=True)
    make_avaliable.short_description = "make avaliable"

    def make_file_unavaliable(self, request, queryset):
        queryset.update(file_avaliable=False)
    make_file_unavaliable.short_description = "make file unavaliable"

    def make_file_avaliable(self, request, queryset):
        queryset.update(file_avaliable=True)
    make_file_avaliable.short_description = "make file avaliable"

    def add_to_collection1(self, request, queryset):
        queryset.update(in_collection=1)

    def add_to_collection2(self, request, queryset):
        queryset.update(in_collection=2)

    def add_to_collection3(self, request, queryset):
        queryset.update(in_collection=3)

    def remove_from_collection(self, request, queryset):
        queryset.update(in_collection=0)

    def update_search_index(self, request, queryset):
        from .search_indexes import ProductIndex
        ex_form = ExtraActionForm(request.POST)
        if ex_form.is_valid() and ex_form.cleaned_data.get('solr_instances'):
            client = solr.SolrConnection(ex_form.cleaned_data['solr_instances'])
            solr_inst = ProductIndex(client)
            solr_inst.reindex_by_qset(queryset, queryset.filter(availability=True))
            client.close()

    def add_to_selected_category(self, request, queryset):
        ex_form = ExtraCategoryForm(request.POST)
        if ex_form.is_valid():
            if str(ex_form.cleaned_data.get('category')) == '-1':
                queryset.update(category=None)
            else:
                queryset.update(category=ex_form.cleaned_data['category'])
        else:
            self.message_user(request, 'Select right category from form', messages.ERROR)

    def mark_products(self, request, queryset):
        queryset.update(marked=True)

    def unmark_products(self, request, queryset):
        queryset.update(marked=False)

    def join_to_cat(self, request, queryset):
        action_id = request.POST.get('action', '').split('add_to_cat_')[-1]
        if action_id.isdigit():
            cat = Category.objects.get(pk=action_id)
            queryset.update(category=cat)

    def changelist_view(self, request, *args, **kwargs):
        cats = Category.get_categories_as_keys()
        cats = dict([(y, '=>'.join(x)) for x, y in cats.items()])
        self._categories_as_keys = cats
        request._getting_changelist = True
        result = super(ProductAdmin, self).changelist_view(request, *args, **kwargs)
        request._getting_changelist = False
        return result

    def get_queryset(self, request):
        qset = super(ProductAdmin, self).get_queryset(request)
        if getattr(request, '_getting_changelist', False):
            # qset = qset.select_related(None)
            qset = qset.defer('shop', 'brand', 'product_description')
        return qset

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super(ProductAdmin, self).get_search_results(request, queryset, search_term)
        if search_term and len(search_term) > 2:
            brands = list(Brand.objects.filter(name__icontains=search_term).values_list('id', flat=True))
            shops = list(Shop.objects.filter(name__icontains=search_term).values_list('id', flat=True))
            kwargs = {'brand__in': brands} if brands else {}
            kwargs.update({'shop__in': shops} if shops else {})
            if kwargs:
                queryset |= queryset.all().filter(**kwargs)
        return queryset, use_distinct

    def remove_and_block(self, request, queryset):
        for item in queryset:
            original_url_hash = md5(item.original_url).hexdigest()
            RemovedItems.objects.get_or_create(data_hash=item.data_hash, original_url_hash=original_url_hash,
                                               defaults={'original_url': item.original_url})
            item.delete()


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ['id', 'tag']
    search_fields = ['tag']


@admin.register(RemovedItems)
class RemovedItemsAdmin(admin.ModelAdmin):
    list_display = ['id', 'original_url', 'original_url_hash', 'data_hash', 'add_time']
    search_fields = ['original_url', '=original_url_hash', '=data_hash']
