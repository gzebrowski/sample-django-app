# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext as _

from treebeard.mp_tree import MP_Node


class Category(MP_Node):
    name = models.CharField(verbose_name=_('name'), max_length=128, help_text=_('enter the name of the category'))
    slug = models.SlugField(verbose_name=_('slug'), max_length=128)
    active = models.BooleanField(verbose_name=_('active'), default=True)
    lead = models.TextField(blank=True)
    keywords = models.CharField(max_length=255, blank=True, help_text=u'metatag for SEO purposes')
    description = models.CharField(max_length=255, blank=True, help_text=u'metatag for SEO purposes')

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['path']

    def __unicode__(self):
        return "%s %s" % (". " * ((self.depth or 1) - 1), self.name)
