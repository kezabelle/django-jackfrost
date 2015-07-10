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


def eventlog_write(sender, instance, read_result, write_result, **kwargs):
    """
    :type sender: jackfrost.models.URLWriter
    :type instance: jackfrost.models.URLWriter
    :type read_result: jackfrost.models.ReadResult
    :type write_result: jackfrost.models.WriteResult
    :type kwargs: dict
    """
    from pinax.eventlog.models import log
    # because `content` may be binary, and is thus a bytes object,
    # we need to remove it, because bytes aren't json encodable, at least
    # under python3.
    read = read_result._asdict()
    read.pop('content')
    return log(user=None,
               action='URL "{url!s}" written'.format(**read_result._asdict()),
               extra={
                   'ReadResult': read,
                   'WriteResult': write_result._asdict(),
               })
