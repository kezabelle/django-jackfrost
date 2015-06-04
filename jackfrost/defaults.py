# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import os
from django.contrib.staticfiles.storage import StaticFilesStorage


__all__ = ['SubfolderStaticFilesStorage', 'JACKFROST_STORAGE',
           'JACKFROST_STORAGE_KWARGS', 'JACKFROST_CONTENT_TYPES']


class SubfolderStaticFilesStorage(StaticFilesStorage):
    def __init__(self, *args, **kwargs):
        super(SubfolderStaticFilesStorage, self).__init__(*args, **kwargs)
        self.location = os.path.join(self.location, 'jackfrost')


JACKFROST_STORAGE = 'jackfrost.defaults.SubfolderStaticFilesStorage'
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
    "text/rss+xml": '.rss',
    "application/rss+xml": '.rss',
    "application/atom+xml": '.atom',
    "application/pdf": '.pdf',
    "text/tab-separated-values": '.tsv',
}
