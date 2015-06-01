# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

JACKFROST_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
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
