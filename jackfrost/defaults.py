# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import os
from django.contrib.staticfiles.storage import StaticFilesStorage


__all__ = ['JackfrostFilesStorage', 'JACKFROST_STORAGE',
           'JACKFROST_STORAGE_KWARGS', 'JACKFROST_CONTENT_TYPES']


class JackfrostFilesStorage(StaticFilesStorage):
    def __init__(self, location=None, *args, **kwargs):
        if location is None:
            from django.conf import settings
            location = os.path.join(settings.BASE_DIR, '__jackfrost')
        super(JackfrostFilesStorage, self).__init__(location, *args, **kwargs)


JACKFROST_STORAGE = 'jackfrost.defaults.JackfrostFilesStorage'
JACKFROST_STORAGE_KWARGS = {}

JACKFROST_CONTENT_TYPES = {
    "text/plain": ".txt",
    "text/html": ".html",
    "text/javascript": ".js",
    "application/javascript": ".js",
    "text/json": ".json",
    "application/json": ".json",
    "text/css": ".css",
    "text/x-markdown": '.md',
    "text/markdown": '.md',
    "text/xml": '.xml',
    "application/xml": '.xml',
    "text/rss+xml": '.rss',
    "application/rss+xml": '.rss',
    "application/atom+xml": '.atom',
    "application/pdf": '.pdf',
    "text/tab-separated-values": '.tsv',
}
