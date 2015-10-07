# -*- coding: utf-8 -*-
from .views import (CollectionPage, PatternCreate, PatternRetrieve,
                    ImagesRetrieve, ImagesComposition, CompositionView,
                    CollectionsView, OneCollectionPage, CollectionUser,
                    GetLastUsersCollections)
from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

urlpatterns = patterns(
    '',
    url(r'^$', CollectionPage.as_view(), name='collection_page'),
    url(r'^pattern-create/$', login_required(csrf_exempt(PatternCreate.as_view())), name='pattern_create'),
    url(r'^pattern-retrieve/$', PatternRetrieve.as_view(), name='pattern_retrieve'),
    url(r'^images-retrieve/$', ImagesRetrieve.as_view(), name='images_retrieve'),
    url(r'^new-composition/$', login_required(csrf_exempt(ImagesComposition.as_view())), name='new_composition'),
    url(r'^get-collection/(?P<pk>[0-9]+)/$', CompositionView.as_view(), name='get_collection'),
    url(r'^list/$', CollectionsView.as_view(), name='collections_list'),
    url(r'^item/(?P<slug>[\w-]*),(?P<pk>[0-9]+)\.htm$', OneCollectionPage.as_view(), name='one_collection_page'),
    url(r'^user/(?P<pk>[0-9]+)/$', CollectionUser.as_view(), name='collection_user'),
    url(r'^users-last-collections/$', GetLastUsersCollections.as_view(), name='users_last_collection'),
)
