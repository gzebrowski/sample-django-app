# -*- coding: utf-8 -*-

import solr
from .base import TaskCommand


class Command(TaskCommand):
    LOG_PROGRESS_STEP = 10

    def run_task(self):
        task_solrs = self.task.solr_instances.all()
        solrs_connections = list(task_solrs.values_list('str_connection', flat=True))
        for conn in solrs_connections:
            client = solr.SolrConnection(conn)
            client.delete_query("*:*")
            client.commit()

    def get_total_items(self):
        return 1
