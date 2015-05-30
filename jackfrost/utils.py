# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from jackfrost.models import URLBuilder

__all__ = ['build_page_for_obj']

def build_page_for_obj(sender, instance, created, **kwargs):
    """
    This may be used as a receiver function for:
        - pre_save
        - post_save
    and will attempt to build the single obj's URL.
    """
    if hasattr(instance, 'jackfrost_absolute_url'):
        url = instance.jackfrost_absolute_url()
    elif hasattr(instance, 'get_absolute_url'):
        url = instance.get_absolute_url()
    else:
        return False

    if hasattr(instance, 'jackfrost_can_build'):
        if instance.jackfrost_can_build() is False:
            return False
    builder = URLBuilder(urls=(url,))
    return builder()
