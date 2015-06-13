# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from django.core.exceptions import ImproperlyConfigured
from jackfrost.models import URLCollector, URLReader, URLWriter

try:
    from celery import shared_task
    from celery import group
except ImportError:
    raise ImproperlyConfigured("You need `celery` installed to use the "
                               "tasks here")


@shared_task
def build_all():
    collected_urls = URLCollector()()
    subtasks = group(build_single.s(url=url) for url in collected_urls)
    results = subtasks()
    return results.get()


@shared_task
def build_single(url):
    read = tuple(URLReader(urls=[url])())
    written = tuple(URLWriter(data=read)())
    return (read, written)
