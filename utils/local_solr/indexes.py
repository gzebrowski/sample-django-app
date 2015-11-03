# -*- coding: utf-8 -*-

import json
import datetime
import logging
import pytz
import traceback
from collections import OrderedDict

logger = logging.getLogger('solrindexer')


def solr_str_escape(val, plus_spaces=False):
    spc_char = '+' if plus_spaces else ' '
    val = val.replace('\\', r'\\')
    if plus_spaces:
        val = val.replace('+', r'\+')
    val = val.replace(' ', r'\%s' % spc_char)
    for c in ['-', '&', '|', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?', ':']:
        val = val.replace(c, '\\%s' % c)
    return val


class BaseField(object):
    def __init__(self, model_attr=None, null=False, index_fieldname=None):
        self.model_attr = model_attr
        self.null = null
        self.index_fieldname = index_fieldname
        self._fname = None

    def to_string(self, val):
        return unicode(val).encode('utf8')

    def to_param(self, val):
        return self.to_string(self.to_python(val))

    def _validate_val(self, val):
        if not self.null and val is None:
            raise ValueError("field %s cannot be null" % (self._fname or '--'))

    def to_python(self, val):
        self._validate_val(val)
        if val is None:
            return None
        return self._to_python(val)

    def _to_python(self, val):
        raise NotImplementedError


class CharField(BaseField):
    def __init__(self, document=False, use_template=False, **kwargs):
        super(CharField, self).__init__(**kwargs)
        self.document = document
        self.use_template = use_template

    def _to_python(self, val):
        return unicode(val)


class FloatField(BaseField):
    def _to_python(self, val):
        return float(val)


class IntegerField(BaseField):
    def _to_python(self, val):
        return int(val)


class MultiValueField(BaseField):
    def _to_python(self, val):
        return list(val)

    def to_param(self, val):
        return self.to_string(val)


class DateTimeField(BaseField):
    def _to_python(self, val):
        if val is not None and not isinstance(val, datetime.datetime):
            raise ValueError
        return val.replace(tzinfo=pytz.UTC)

    @classmethod
    def to_string(cls, val):
        if isinstance(val, datetime.datetime):
            return val.isoformat().split('.')[0]


class SearchMetaClass(type):
    def __new__(cls, name, bases, attrs):
        my_fields = []
        newattrs = {'fields': {}}
        for k, v in attrs.items():
            if isinstance(v, BaseField):
                v._fname = k
                my_fields.append((k, v))
            else:
                newattrs[k] = v
        if my_fields:
            newattrs['fields'] = OrderedDict(my_fields)
        else:
            newattrs = attrs
        return super(SearchMetaClass, cls).__new__(cls, name, bases, newattrs)


class SearchIndex(object):
    __metaclass__ = SearchMetaClass
    COMMIT_PER = 200
    AUTOCOMMIT = False
    UNIQUE_FIELD = None
    DB_STEP = 500
    RUN_IN_PARALLEL = False

    def __init__(self, client, *args, **kwargs):
        self.using = kwargs.get('using', None)
        self.args = args
        self.kwargs = kwargs
        self.item_callback = kwargs.get('item_callback', None)
        self.client = client
        self.start_from = kwargs.get('start_from', 0)
        self.db_step = int(kwargs.get('db_step', self.DB_STEP))
        self.commit_per = int(kwargs.get('commit_per', self.COMMIT_PER))
        self.run_in_parallel = kwargs.get('run_in_parallel', self.RUN_IN_PARALLEL)
        self._buffer = []
        self.items_sent = 0

    def process_part(self, rng, step, queryset=None):
        qset = queryset.all()[rng:rng + step] if queryset is not None else self.index_queryset(using=self.using)[rng:rng + step]
        for no, obj in enumerate(qset):
            self.process_object(obj)
            if not self.AUTOCOMMIT:
                self.commit()

    def process_record(self, data):
        if isinstance(data, (list, tuple)):
            self.client.add_many(data)
            if not self.AUTOCOMMIT:
                self.commit()
        elif isinstance(data, dict):
            if self.run_in_parallel:
                if len(self._buffer) >= self.commit_per:
                    self.flush()
                self._buffer.append(data)
            else:
                self.client.add(**data)
                self.items_sent += 1
                if self.items_sent > self.commit_per:
                    self.flush()

    def flush(self):
        if self._buffer:
            self.client.add_many(self._buffer)
        if not self.AUTOCOMMIT and (self._buffer or self.items_sent):
            self.commit()
        self._buffer = []
        self.items_sent = 0

    def commit(self):
        self.client.commit()

    def process_object(self, obj):
        data = self.prepare_data(obj)
        error = None
        try:
            self.process_record(data)
        except Exception, e:
            trb = traceback.format_exc()
            body = unicode(getattr(e, 'body', '!! No exception body supplied !!'))
            msg = '%s\n%s\n%s' % (unicode(e), body, trb)
            logger.error(msg)
            error = {'traceback': trb, 'body': body, 'e': unicode(e), 'data': data}
        if self.item_callback:
            self.item_callback(obj, error=error)

    def run(self):
        qset = self.index_queryset(using=self.using)
        self.index_by_qset(qset)
        self.flush()

    def reindex_by_qset(self, del_qset, index_qset=None):
        index_qset = index_qset or del_qset.all()
        self.delete_by_qset(del_qset)
        self.index_by_qset(index_qset)
        self.commit()

    def delete_by_qset(self, qset):
        fields = [x[1] for x in self.fields.items() if x[0] == self.UNIQUE_FIELD]
        if len(fields) != 1:
            raise Exception('Missing unique field')
        field = fields[0]
        model_attr = getattr(field, 'model_attr') or self.UNIQUE_FIELD
        solr_field = getattr(field, 'index_fieldname') or self.UNIQUE_FIELD
        for nr, item in enumerate(qset.only(model_attr)):
            self.client.delete_query("%s:%s" % (solr_field, solr_str_escape(getattr(item, model_attr))))
            if not (nr % 1000) and nr:
                self.client.commit()
        self.client.commit()

    def index_by_qset(self, qset):
        cnt = qset.count()
        for rng in xrange(self.start_from, cnt, self.db_step):
            self.process_part(rng, self.db_step, queryset=qset)

    def prepare_data(self, obj):
        result = {}
        for field, f_ins in self.fields.items():
            solr_field = f_ins.index_fieldname or field
            if f_ins.model_attr:
                try:
                    val = f_ins.to_python(getattr(obj, f_ins.model_attr))
                except Exception:
                    logger.error("error with field: %s\n%s" % (field, traceback.format_exc()))
                    raise
            else:
                val_getter = getattr(self, 'prepare_%s' % field, None)
                if val_getter is None:
                    continue
                try:
                    val = f_ins.to_python(val_getter(obj))
                except Exception:
                    logger.error("error with field: %s\n%s" % (field, traceback.format_exc()))
                    raise
            result[solr_field] = val
        return result

    def simple_filter(self, _params=None, **kwargs):
        q = kwargs.pop('_q', '*')
        _params = _params or {}
        new_kwargs = {}
        for k in kwargs:
            f = self.fields[k]
            new_kwargs[f.index_fieldname or k] = f.to_param(kwargs[k])
        result_r = self.query_builder(query=q, fq=new_kwargs, **_params)
        result = result_r['response']['docs']
        cnt = result_r['response']['numFound']
        new_result = []
        fields = dict([(x[1].index_fieldname or x[0], x[0]) for x in self.fields.items()])
        for item in result:
            print item
            p = {}
            for k in item:
                field_name = fields.get(k)
                if field_name:
                    try:
                        p[field_name] = self.fields[field_name].to_python(item[k])
                    except ValueError:
                        p[field_name] = None
            new_result.append(p)
        return {'docs': new_result, 'count': cnt}

    def query_builder(self, query='*:*', result_format="json", facet=None,
                      escape='all', fq=None, extra_params=None, fq_list=None, **kwargs):  # TODO: needs to be enhanced
        '''
            Simple tool to build solr query
            fq: it is a dictionary with {field: value}
            facet_fields: fields to faceting
            escape: if 'spaces', then changes only ' ' to r'\ ', if all, then escapes spaces and uses urllib.quote_plus
        '''
        assert escape in (False, 'all')
        assert facet is None or isinstance(facet, dict)
        facet = facet or {}
        extra_params = extra_params or {}
        _esc = {False: lambda x: x, 'all': lambda x: solr_str_escape(x)}[escape]
        payload = {'wt': result_format or ''}
        if facet:
            for fkey in facet:
                fval = facet[fkey]
                if fkey == 'field':
                    if isinstance(fval, basestring):
                        fval = [fval]
                    elif isinstance(fval, (list, tuple)):
                        fval = list(fval)
                payload.update({'facet.%s' % fkey: fval})
            payload['facet'] = 'on'
        if query:
            payload['q'] = query
        if fq:
            assert isinstance(fq, dict)
            payload['fq'] = map(lambda x: "%s:%s" % (x[0], _esc(x[1])), fq.items())
        elif fq_list:
            payload['fq'] = fq_list
        payload.update(extra_params)
        payload.update(kwargs)
        resp = self.client.raw_query(**payload)
        if result_format.lower() == 'json':
            return json.loads(resp)
        elif result_format.lower() == 'python':
            return eval(resp)
        return resp


class Indexable(object):
    pass
