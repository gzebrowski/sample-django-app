# -*- coding: utf-8 -*-

from django import template

register = template.Library()


@register.filter
def turn_to_absolute_url(value):
    return value  # fake filter
