# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from jackfrost.models import ModelRenderer
from jackfrost.models import URLReader
from jackfrost.models import URLWriter

__all__ = ['build_page_for_obj']


def build_page_for_obj(sender, instance, **kwargs):
    """
    This may be used as a receiver function for:
        - pre_save
        - post_save
    and will attempt to build the single obj's URL.
    """

    class PseudoModelRenderer(ModelRenderer):
        def get_paginated_queryset(self):
            return (instance,)

    instance_urls = PseudoModelRenderer()()
    read = tuple(URLReader(urls=instance_urls)())
    written = tuple(URLWriter(data=read)())
    return (read, written)
