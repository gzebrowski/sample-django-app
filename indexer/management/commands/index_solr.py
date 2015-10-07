# -*- coding: utf-8 -*-

from product.models import Product
from product.search_indexes import ProductIndex
from .index_solr_base import SolrCommandBase
from optparse import make_option


class Command(SolrCommandBase):
    LOG_PROGRESS_STEP = 50
    my_model = Product
    my_index_model = ProductIndex
    option_list = SolrCommandBase.option_list + (
        make_option('--only-marked',
                    dest='only_marked',
                    action='store_true',
                    default=False,
                    help='only marked products'),
        make_option('--only-unmarked',
                    dest='only_unmarked',
                    action='store_true',
                    default=False,
                    help='only unmarked products'),
    )

    def item_processed2(self, obj, error=None):
        self.item_processed()
        if error:
            self.log_list.append("%s | %s | %s\n" % (error.get('e', ''), error.get('body', ''), error.get('data', {}).get('id', '')))
            if not obj.data_error:
                obj.data_error = True
                obj.save()
        elif obj.data_error:
            obj.data_error = False
            obj.save()
        if self.items_processed % 300 == 0:
            self.reconnect_client()

    def get_my_callback(self):
        return self.item_processed2

    def get_extra_kwargs(self):
        kwargs = {}
        kwargs.update({'marked': True} if self.options['only_marked'] else {})
        kwargs.update({'marked': False} if self.options['only_unmarked'] else {})
        return {'extra_filters': kwargs} if kwargs else {}
