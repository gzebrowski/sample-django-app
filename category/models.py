# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext as _
from django.template.defaultfilters import slugify

from treebeard.mp_tree import MP_Node


class Category(MP_Node):
    name = models.CharField(verbose_name=_('name'), max_length=128, help_text=_('enter the name of the category'))
    slug = models.SlugField(verbose_name=_('slug'), max_length=128)
    active = models.BooleanField(verbose_name=_('active'), default=True)
    lead = models.TextField(blank=True)
    keywords = models.CharField(max_length=255, blank=True, help_text=u'metatag for SEO purposes')
    description = models.CharField(max_length=255, blank=True, help_text=u'metatag for SEO purposes')
    steplen = 2

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['path']

    def __unicode__(self):
        return "%s %s" % (". " * ((self.depth or 1) - 1), self.name)

    @classmethod
    def get_categories_as_keys(cls, refresh=False):
        if not refresh and getattr(cls, '_categories_as_keys', None):
            return cls._categories_as_keys
        all_categories = list(cls.objects.all().order_by('path').values())
        gcats = {}
        category_ids = {}
        for c in all_categories:
            gcats[c['path']] = c
        for c in gcats:
            all_keys = [gcats.get(c[:x]) for x in range(cls.steplen, len(c) + 1, cls.steplen)]
            all_keys = map(lambda x: slugify(x['name']) if x else '', all_keys)
            if len(filter(None, all_keys)) == len(all_keys):
                category_ids[tuple(all_keys)] = gcats[c]['id']
        cls._categories_as_keys = category_ids
        return category_ids

    def save(self, *args, **kwargs):
        self.__class__._categories_as_keys = None
        return super(Category, self).save(*args, **kwargs)
