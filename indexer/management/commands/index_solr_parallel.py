# -*- coding: utf-8 -*-

from product.models import Product
from product.search_indexes import ProductIndex
from .index_solr_base import SolrCommandBase
from optparse import make_option
from utils.utils import is_this_mine


class MultiNodeProductIndex(ProductIndex):
    AUTOCOMMIT = True

    def process_part(self, rng, step, *args, **kwargs):
        if not self.kwargs.get('multiinstance_mode') or is_this_mine(rng):
            return super(MultiNodeProductIndex, self).process_part(
                rng, step, *args, **kwargs)
        else:
            if self.item_callback:
                for x in range(step):
                    self.item_callback(None)


class Command(SolrCommandBase):
    LOG_PROGRESS_STEP = 50
    my_model = Product
    my_index_model = MultiNodeProductIndex
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
        make_option('--multiinstance-mode',
                    dest='multiinstance_mode',
                    action='store_true',
                    default=False,
                    help='run in parallel on all dashboard nodes'),
        make_option('--commit-per',
                    dest='commit_per',
                    default=200,
                    type='int',
                    help='solr commit per documents'),
        make_option('--db-step',
                    dest='db_step',
                    default=5000,
                    type='int',
                    help='db step'),
    )

    def run_task(self):
        from indexer.models import WorkingTask
        not_mm = not self.options.get('multiinstance_mode')
        if not_mm and WorkingTask.objects.filter(
                work_type=self.task.work_type,
                status__in=[WorkingTask.STATUS_NEW,
                            WorkingTask.STATUS_IN_PROGRESS]).exclude(
                                pk=self.task.pk).exists():
            raise RuntimeError("There can be only one running instance if multiinstance_mode isn't chosen")
        return super(Command, self).run_task()

    def item_processed2(self, obj, error=None):
        self.item_processed()
        if not obj:
            return
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
        commit_per = self.options.get('commit_per') or 200
        db_step = self.options.get('db_step') or 5000
        multiinstance_mode = self.options.get('multiinstance_mode')
        result = {'run_in_parallel': True, 'commit_per': commit_per,
                  'db_step': db_step, 'multiinstance_mode': multiinstance_mode}
        kwargs = {}
        kwargs.update({'marked': True} if self.options['only_marked'] else {})
        kwargs.update({'marked': False} if self.options['only_unmarked'] else {})
        result.update({'extra_filters': kwargs} if kwargs else {})
        return result
