# -*- coding: utf-8 -*-

import datetime
import os
import json
import math
import re

from django.views.generic.base import View, TemplateView
# from django.views.generic.edit import CreateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from .models import (Pattern, PatternElement, MyValueField, Composition,
                     CompositionElement, prepare_product_url,
                     my_value_fields, LastUserCoComposition)
from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import get_storage_class
from product.search_indexes import ProductIndex
from userprofile.models import ProfileUser

global_storage = get_storage_class(settings.GLOBAL_FILE_STORAGE)()
path_join = lambda *p: os.path.join(*p).replace('\\', '/')


class CollectionPage(TemplateView):
    template_name = 'collection/collection_test.html'


class PatternCreate(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
        except Exception:
            raise
            return JsonResponse({'status': 'error'})
        try:
            obj = Pattern.objects.create(author=request.user, name=data['name'])
            items = data['items']
        except:
            raise
            return JsonResponse({'status': 'error'})
        else:
            my_fields = [(f.name, f.value_retriever()) for f in PatternElement._meta.fields if isinstance(f, MyValueField)]
            for item in items:
                kw = {'pattern': obj}
                for my_field in my_fields:
                    try:
                        kw[my_field[0]] = my_field[1](item.get(my_field[0]))
                    except Exception:
                        pass
                    if kw.get('background_image'):
                        assert re.search(r'^/[a-z0-9_-][a-z0-9_/-]*[a-z0-9_-]+\.[a-z0-9]+$', kw['background_image'])
                PatternElement.objects.create(**kw)
            try:
                obj.create_thumbnail()
            except Exception:
                obj.delete()
                return JsonResponse({'status': 'FAILED'})
            else:
                obj.save()
            return JsonResponse({'status': 'OK'})


class ImagesComposition(View):
    def post(self, request, *args, **kwargs):
        # my_fields = [f.name[len('image_'):] for f in CompositionElement._meta.fields if isinstance(f, MyValueField) and f.name.startswith('image_')]
        my_fields = [x[len('image_'):] for x in my_value_fields(CompositionElement) if x.startswith('image_')]
        try:
            data = json.loads(request.body)
        except Exception:
            raise
            return JsonResponse({'status': 'error'})
        pid = data.get('pid')
        name = data.get('name')
        obj = Composition.objects.create(pattern_id=pid, author=request.user, name=name)
        for item in data.get('items'):
            kwargs = dict([('image_' + k, item.get(k)) for k in my_fields])
            if kwargs.get('image_url') and not re.search(r'^/[a-z0-9_-][a-z0-9_/-]*[a-z0-9_,-]+\.html?$', kwargs['image_url']):
                # raise Exception
                continue  # FIXME
            CompositionElement.objects.create(composition=obj, pattern_element_id=item['id'], **kwargs)
        try:
            obj.create_thumbnail()
        except Exception:
            obj.delete()
            return JsonResponse({'status': 'FAILED'})
        else:
            obj.save()
            # normaly there should be used a signal, but this will have to be moved to flask
            # LastUserCoComposition.objects(user_id=current_user_id).update(set__last_created=datetime.datetime.now(), set__composition=obj.id, upsert=True)
            el, created = LastUserCoComposition.objects.get_or_create(author=request.user)
            el.last_created = datetime.datetime.now()
            el.composition_ids = ','.join(map(str, ([obj.id] + map(int, filter(None, el.composition_ids.split(','))))[:3]))
            el.save()
        return JsonResponse({'status': 'OK'})


class PatternRetrieve(View):
    def get(self, request):
        result = []
        p = int(request.GET.get('p') or 0)
        step = 15
        my_fields = my_value_fields(PatternElement)
        my_fields += ['id']
        qset = Pattern.objects.all()
        cnt = qset.count()
        cnt /= step
        for p in qset[p * step:(p + 1) * step]:
            res_item = {'name': p.name, 'id': p.id, 'thumbnail': p.my_thumbnail, 'items': []}
            items = list(p.patternelement_set.all().values(*my_fields))
            res_item['items'] = items
            result.append(res_item)
        return JsonResponse({'result': result, 'totalPages': cnt})


class ImagesRetrieve(View):
    def get(self, request):
        from utils.local_solr.connector import solr_client
        pi = ProductIndex(solr_client)
        q = request.GET.get('q') or '*'
        p = int(request.GET.get('p') or 0)
        main_category = request.GET.get('mc') or ''
        country = request.GET.get('c') or ''
        country_map = {'usa': 'united-states', 'uk': 'united-kingdom'}
        country = country_map.get(country)
        kwargs = {}
        if country:
            kwargs['country_slug'] = country
        if main_category:
            kwargs['main_category'] = main_category
        step = 12
        start = p * step
        fields = 'product_name product_title_slug product_img main_category product_brand brand_slug product_id relative_image_filepath in_collection id country_slug'
        result_set = pi.simple_filter(in_collection=1, _q=q, _params={'start': start, 'rows': step, 'fl': fields}, **kwargs)
        new_result_set = []
        for d in result_set['docs']:
            try:
                pth = os.path.splitext(path_join('transparent', d['relative_image_filepath']))[0] + '.png'
                d['path'] = global_storage.url(pth)
                d['id'] = d['product_id']
                d['url'] = prepare_product_url(d)
                new_result_set.append(d)
            except Exception:
                pass
        max_pages = int(math.ceil(float(result_set['count']) / step))
        return JsonResponse({'result': new_result_set, 'count': result_set['count'], 'p': p, 'max_pages': max_pages})


class CompositionView(DetailView):
    queryset = Composition.objects.filter(active=True)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        result = obj.get_elements_as_json()
        return JsonResponse({'name': obj.name, 'items': result})


class CollectionsView(ListView):
    template_name = 'collection/collection_presentation.html'
    model = Composition
    paginate_by = 50


class GetLastUsersCollections(ListView):
    model = LastUserCoComposition
    paginate_by = 20
    template_name = 'collection/users_last_collections.html'

    def get_context_data(self, **kwargs):
        context = super(GetLastUsersCollections, self).get_context_data(**kwargs)
        objects = list(self.get_queryset())
        result = []
        all_collection_list = []
        item, curr_no = None, 0
        for x in objects:
            all_collection_list.extend(map(int, x.composition_ids.split(',')))
        all_comp = Composition.objects.filter(pk__in=all_collection_list).order_by('author', '-add_time')
        for el in all_comp:
            if item is None or item['author'] != el.author:
                if item is not None:
                    result.append(item)
                item = {'author': el.author, 'title': el.name, 'items': {}}
                curr_no = 0
            item['items']['o_%s' % curr_no] = el
            curr_no += 1
        if item:
            result.append(item)
        context['collections_by_users'] = result
        return context


class CollectionUser(ListView):
    model = Composition
    paginate_by = 20
    template_name = 'collection/collection_user_list.html'

    def get_queryset(self):
        qset = super(CollectionUser, self).get_queryset()
        qset = qset.filter(author_id=self.kwargs['pk'])
        return qset

    def get_context_data(self, **kwargs):
        context = super(CollectionUser, self).get_context_data(**kwargs)
        user = ProfileUser.objects.get(pk=self.kwargs['pk'])
        context['author'] = user
        return context


class OneCollectionPage(DetailView):
    model = Composition
    template_name = 'collection/collection_page.html'
