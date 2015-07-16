# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from django.core.exceptions import ImproperlyConfigured
from jackfrost.models import collect, read, write

try:
    from celery import shared_task
    from celery import group
except ImportError:
    raise ImproperlyConfigured("You need `celery` installed to use the "
                               "tasks here")


@shared_task
def build_all():
    collected_urls = collect()
    subtasks = group(build_single.s(url=url) for url in collected_urls)
    results = subtasks()
    return results.get()


@shared_task
def build_single(url):
    read_ = tuple(read(urls=[url]))
    written = tuple(write(data=read_))
    return (read_, written)
