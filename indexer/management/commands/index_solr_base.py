# -*- coding: utf-8 -*-

import solr
from .base import TaskCommand
from indexer.models import Log


class SolrCommandBase(TaskCommand):
    LOG_PROGRESS_STEP = 50
    my_model = None
    my_index_model = None

    def run_task(self):
        if not self.solrs_connections:
            self.add_log("Solr connection wasn't chosen", tp=Log.LOGTYPE_WARNING)
            return
        start_val = self.task.items_processed
        for conn_str in self.solrs_connections:
            self.curr_conn_str = conn_str
            self.reconnect_client()
            pr_idx = self.my_index_model(self.client, item_callback=self.get_my_callback(),
                                         start_from=start_val, **self.get_extra_kwargs())
            pr_idx.run()

    def get_extra_kwargs(self):
        return {}

    def reconnect_client(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        self.client = solr.SolrConnection(self.curr_conn_str)

    def get_my_callback(self):
        return None

    def init(self):
        self.log_list = []
        task_solrs = self.task.solr_instances.all()
        self.solrs_connections = list(task_solrs.values_list('str_connection', flat=True))
        self.client = None
        # self.reconnect_client()

    def get_total_items(self):
        return len(self.solrs_connections) * self.my_model.objects.filter(availability=True).count()

    def after_finish(self):
        if self.log_list:
            self.add_log("Failed to index %s items:\r\n%s" % (len(self.log_list), '\n'.join(self.log_list)), tp=Log.LOGTYPE_WARNING)
