# -*- coding: utf-8 -*-

import os
import shutil

from django.conf import settings

from optparse import make_option
import solr
from .base import TaskCommand
from product.models import Product
from utils.utils import is_my_file
from django.core.files.storage import get_storage_class


class Command(TaskCommand):
    option_list = TaskCommand.option_list + (

        make_option('--clean-fs',
                    action='store_true',
                    dest='clean_filesystem',
                    default=False,
                    help='clean from filesystem'),
        make_option('--clean-mogile',
                    action='store_true',
                    dest='clean_mogile',
                    default=False,
                    help='clean from mogilefs'),
        make_option('--clean-mogile-nodes',
                    action='store_true',
                    dest='clean_up_mogile_nodes',
                    default=False,
                    help='clean up mogilefs nodes after rebuilding nodeset'),
        make_option('--use-mogile-node',
                    action='store',
                    type='string',
                    dest='use_mogile_node',
                    default=None,
                    help='use specific mogilefs node name - this option works only with --clean-mogile-nodes or --clean-mogile'),
        make_option('--use-existing-list',
                    action='store_true',
                    dest='useexisting',
                    default=False,
                    help='use existing list'),
        make_option('--use-database',
                    action='store_true',
                    dest='usedatabase',
                    default=False,
                    help='use database instead of solr'),
    )

    def get_lines_by_params(self, is_transparent, part):
        if is_transparent:
            part = filter(lambda x: x and x[0] == '1', part)
        return map(lambda x: x[2:], part)

    def run_task(self):
        result = {}

        len_storage_root = len(self.storage_root)
        for k in ['TMPDIR', 'TEMP', 'TMP']:
            tmp_dir = os.environ.get(k)
            if tmp_dir:
                break
        tmp_dir = tmp_dir or '/tmp'
        filelist_path = os.path.join(tmp_dir, 'temporary_filelist')
        if not os.path.exists(filelist_path):
            os.makedirs(filelist_path)
        if self.options['useexisting']:
            for f in os.listdir(filelist_path):
                cnt = open(os.path.join(filelist_path, f), 'r').read()
                k = f.split('_', 1)[0]
                if not k.isdigit():
                    continue
                result[k] = filter(None, [ff.strip() for ff in cnt.split('\r\n')])
            if not result:
                print "no files in temporary dir"
                return
        else:
            start = 0
            rows_cnt = 10000
            s = None
            if not self.options['usedatabase']:
                task_solrs = self.task.solr_instances.all()
                solrs_connections = list(task_solrs.values_list('str_connection', flat=True))
                if not solrs_connections:
                    return
                s = solr.SolrConnection(solrs_connections[0])

            def get_rows(start, limit, s):
                if self.options['usedatabase']:
                    return 'relative_img_path', Product.objects.filter(availability=True).values('relative_img_path', 'in_collection')[start:start + limit]
                else:
                    return 'relative_image_filepath', s.query('*:*', fq=["relative_image_filepath:*"],
                                                              fields=["relative_image_filepath in_collection"],
                                                              rows=limit, start=start).results
            while True:
                img_path_key, rows = get_rows(start, rows_cnt, s)
                try:
                    lines = [('1_' if r['in_collection'] else '0_') + r[img_path_key] for r in rows]
                    assert lines
                except (KeyError, TypeError, ValueError, AssertionError):
                    break
                for l in lines:
                    key_tmp = l.split('_', 1)[1].lstrip('/')
                    if not is_my_file(key_tmp):
                        continue
                    key = key_tmp.split('/', 1)[0]
                    if key not in result:
                        result[key] = []
                    result[key].append(os.path.splitext(l)[0])
                start += rows_cnt
            for f in os.listdir(filelist_path):
                os.remove(os.path.join(filelist_path, f))
            all_keys = sorted(result.keys())
            for k in all_keys:
                f = open(os.path.join(filelist_path, k + '_files.dat'), 'w')
                f.write('\r\n'.join(sorted(result[k])))

        start_from = self.task.items_processed
        total_processed = 0
        if self.options['clean_mogile']:
            selected_node = self.options.get('use_mogile_node') or None
            extra_kwargs = {'node': selected_node} if selected_node else {}
            for d2p in self.dirs_to_process:
                len2 = len(d2p) + (1 if d2p else 0)
                for k in range(1000):
                    k2 = "%0.3d" % k
                    k3 = os.path.join(d2p, k2)
                    mog_files = self.global_storage.listfiles(k3, **extra_kwargs)
                    result_k2 = self.get_lines_by_params(d2p, result[k2])
                    for f in mog_files:
                        total_processed += 1
                        if start_from >= total_processed:
                            continue
                        if not is_my_file(f):
                            self.item_processed()
                            continue
                        if os.path.splitext(f[len2:])[0] not in result_k2:
                            self.try_to_execute(self._delete, args=[f], except_func=self._reconect_mogile)
                            try:
                                assert d2p == ''
                                thums_list_keys = self.global_storage.listfiles(os.path.join('thumbnails', k2), **extra_kwargs)
                            except Exception:
                                pass
                            else:
                                for thmb in thums_list_keys:
                                    self.try_to_execute(self._delete, args=[thmb], except_func=self._reconect_mogile)
                        self.item_processed()
        if self.options['clean_up_mogile_nodes'] and hasattr(self.global_storage, 'listfiles_with_nodes'):
            selected_node = self.options.get('use_mogile_node') or None
            for d2p in self.dirs_to_process:
                len2 = len(d2p) + (1 if d2p else 0)
                for k in range(1000):
                    k2 = "%0.3d" % k
                    k3 = os.path.join(d2p, k2)
                    mog_files = self.global_storage.listfiles_with_nodes(k3, node=selected_node)
                    for f, node, is_mine in mog_files:
                        total_processed += 1
                        if start_from >= total_processed:
                            continue
                        if is_mine:
                            self.item_processed()
                            continue
                        self.try_to_execute(self._delete, args=[f], kwargs={'node': node}, except_func=self._reconect_mogile)
                        try:
                            assert d2p == ''
                            thums_list_keys = self.global_storage.listfiles_with_nodes(os.path.join('thumbnails', k2), node=selected_node)
                        except Exception:
                            pass
                        else:
                            for thmb, node2, is_mine2 in thums_list_keys:
                                if not is_mine2:
                                    self.try_to_execute(
                                        self._delete, args=[thmb], kwargs={'node': node2},
                                        except_func=self._reconect_mogile)
                        self.item_processed()
        if self.options['clean_filesystem']:
            for d2p in self.dirs_to_process:
                len_storage_root2 = len_storage_root + len(d2p) + (1 if d2p else 0)
                src_path = os.path.join(self.storage_root, d2p)
                for f in os.listdir(src_path):
                    curr_dir = os.path.join(src_path, f)
                    if not f.isdigit() or len(f) != 3 or not os.path.isdir(curr_dir):
                        continue
                    result_f = self.get_lines_by_params(d2p, result[f])
                    for base_dir, subdirs, dirfiles in os.walk(curr_dir):
                        for f2 in dirfiles:
                            total_processed += 1
                            if start_from >= total_processed:
                                continue
                            curr_f = os.path.join(base_dir, f2)
                            try:
                                assert os.path.splitext(curr_f[len_storage_root2:])[0] in result_f
                            except (AssertionError, KeyError):
                                os.remove(curr_f)
                                if not os.listdir(base_dir):
                                    os.rmdir(base_dir)
                                if d2p == '':
                                    thmb_path = base_dir.replace(
                                        self.storage_root, self.storage_root + 'thumbnails/', 1)
                                    thmb_path = os.path.dirname(thmb_path)
                                    try:
                                        shutil.rmtree(thmb_path)
                                    except Exception:
                                        pass
                            self.item_processed()

    def get_total_items(self):
        cnt = 0
        if self.options['clean_filesystem']:
            for d2p in self.dirs_to_process:
                src_path = os.path.join(self.storage_root, d2p)
                for f in os.listdir(src_path):
                    curr_dir = os.path.join(src_path, f)
                    if not f.isdigit() or len(f) != 3 or not os.path.isdir(curr_dir):
                        continue
                    for base_dir, subdirs, dirfiles in os.walk(curr_dir):
                        for f2 in dirfiles:
                            cnt += 1
        if self.options['clean_mogile']:
            myrange = ['%0.3d/' % x for x in range(1000)]
            for d2p in self.dirs_to_process:
                for k in myrange:
                    keys = self.global_storage.listfiles(os.path.join(d2p, k))
                    cnt += len(keys)
        return cnt

    def init(self):
        self.storage_root = settings.STORAGE_ROOT.rstrip('/') + '/'
        self.global_storage = get_storage_class(settings.GLOBAL_FILE_STORAGE)()
        self.dirs_to_process = ['', 'transparent']
        if self.options['clean_mogile']:
            self._reconect_mogile()

    def _reconect_mogile(self):
        self.global_storage = get_storage_class(settings.GLOBAL_FILE_STORAGE)()

    def _delete(self, val, **kwargs):
        self.global_storage.delete(val, **kwargs)
