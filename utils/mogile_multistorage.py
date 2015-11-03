# -*- coding: utf-8 -*-

import random
import datetime
import os
from django.conf import settings
from django.core.files import File
from pymogile import Client, MogileFSError  # noqa
from hash_ring import HashRing


def get_random_string(num):
    return str(random.randrange(10 ** num))


class MyIterator(object):
    def __init__(self, obj, path, match=False, node=None):
        self.obj = obj
        self.path = path
        self.match = match
        self.node = node

    def _iter_nodes(self):
        path = (self.path.strip('/') + '/') if not self.match else self.path
        the_nodes = [self.node] if self.node else self.obj.servers.keys()
        for node in the_nodes:
            self.current_node = node
            try:
                keys = self.obj.clients[node].list_keys(path)
            except MogileFSError:
                continue
            yield keys

    def __iter__(self):
        for keys in self._iter_nodes():
            for f in keys:
                yield f

    def __len__(self):
        if getattr(self, '_my_length', None):
            return self._my_length
        ln = 0
        for f in self._iter_nodes():
            ln += len(f)
        self._my_length = ln
        return ln


class MyNodeIterator(MyIterator):
    def __iter__(self):
        for keys in self._iter_nodes():
            for f in keys:
                yield (f, self.current_node, self.obj.get_key_by_name(f) == self.current_node)


class MogileFSMultiStorage(object):
    """
    MogileFS filesystem storage
    """

    def __init__(self, location=None, base_url=None, **kwargs):
        self.clients = {}
        for server in settings.DISTRIBUTED_MOGILEFS_CONFIG['SERVERS']:
            srv = settings.DISTRIBUTED_MOGILEFS_CONFIG['SERVERS'][server]
            self.clients[server] = Client(domain=srv['DOMAIN'], trackers=srv['TRACKERS'])
        self.servers = settings.DISTRIBUTED_MOGILEFS_CONFIG['SERVERS']
        self.ring = HashRing(settings.DISTRIBUTED_MOGILEFS_CONFIG['SLOTS'])
        self.kwargs = kwargs

    def open(self, name, mode='rb', node=None, **kwargs):
        """
        Retrieves the specified file from storage.
        """
        name = self.filepath(name)
        if not name:
            return None
        key = node or self.get_key_by_name(name, **kwargs)
        if mode != 'rb':
            raise Exception('only "rb" mode is supported')
        return File(self.clients[key].read_file(name))

    def save(self, name, content, node=None, **kwargs):
        """
        Saves new content to the file specified by name. The content should be
        a proper File object or any python file-like object, ready to be read
        from the beginning.
        """
        # Get the proper name for the file, as it will actually be saved.
        if name is None:
            name = content.name

        # if not hasattr(content, 'read'):
        #    content = File(content)

        name = self.get_available_name(name)
        if hasattr(content, 'read') and callable(content.read):
            if hasattr(content, 'seek') and callable(content.seek):
                content.seek(0)
            content = content.read()

        name = self._save(name, content, node=node, **kwargs)

        # Store filenames with forward slashes, even on Windows
        return name.replace('\\', '/')

    # These methods are part of the public API, with default implementations.

    def get_available_name(self, name):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        # If the filename already exists, add an underscore and a random 7
        # character alphanumeric string (before the file extension, if one
        # exists) to the filename until the generated filename doesn't exist.
        while self.exists(name):
            # file_ext includes the dot.
            name = os.path.join(dir_name, "%s_%s%s" % (file_root, get_random_string(7), file_ext))

        return name

    def _save(self, name, content, node=None, **kwargs):
        name = self.filepath(name)
        if not name:
            return name
        key = node or self.get_key_by_name(name, **kwargs)
        fp = self.clients[key].new_file(name.lstrip('/'))
        fp.write(content)
        fp.close()
        return name

    def delete(self, name, node=None, **kwargs):
        assert name, "The name argument is not allowed to be empty."
        name = self.filepath(name)
        if name:
            key = node or self.get_key_by_name(name, **kwargs)
            self.clients[key].delete(name)

    def remove(self, name, node=None, **kwargs):
        return self.delete(name, node=node, **kwargs)

    def exists(self, name, node=None, **kwargs):
        name = self.filepath(name)
        if not name:
            return False
        key = node or self.get_key_by_name(name, **kwargs)
        return bool(self.clients[key].get_paths(name))

    def listdir(self, path):
        raise NotImplementedError

    def listfiles(self, path, node=None):
        return MyIterator(self, path, False, node=node)

    def listfiles_startswith(self, path, node=None):
        return MyIterator(self, path, True, node=node)

    def listfiles_with_nodes(self, path, node=None):
        return MyNodeIterator(self, path, True, node=node)

    def path(self, name):
        return os.path.normpath(name.replace('\\', '/')).replace('\\', '/')

    def filepath(self, name):
        name = self.path(name)
        if name.endswith('/'):
            return ''
        return name

    def size(self, name, node=None, **kwargs):
        name = self.filepath(name)
        key = node or self.get_key_by_name(name, **kwargs)
        return len(self.clients[key].read_file(name).read())

    def get_key_by_name(self, name, **kwargs):
        return self.ring.get_node(name)

    def url(self, name, node=None, **kwargs):
        name = self.path(name)
        if not name:
            return ''
        node_key = node or self.get_key_by_name(name, **kwargs)
        name = name.lstrip('/')
        urls = self.servers[node_key]['URLS']
        urls = [urls] if isinstance(urls, basestring) else urls
        if len(urls) > 1:
            ring2 = HashRing(urls)
            base_url = ring2.get_node(node_key)
        else:
            base_url = urls[0]
        return base_url + name

    def accessed_time(self, name):
        return datetime.datetime.now()

    def created_time(self, name):
        return datetime.datetime.now()

    def modified_time(self, name):
        return datetime.datetime.now()

    def get_storage_domains(self):
        return self.storage_domains
