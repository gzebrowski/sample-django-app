# -*- coding: utf-8 -*-

from django.conf import settings
import solr

solr_client = solr.SolrConnection(settings.SOLR_URL['default'])
