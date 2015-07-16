# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from os.path import splitext


def is_url_usable(url):
    """
    A URL must end in a slash or a file extension to be usable by
    a webserver.
    >>> assert is_url_usable('/a/b/c/') is True
    >>> assert is_url_usable('/a/b/c.html') is True
    >>> assert is_url_usable('/a/b.json') is True
    >>> assert is_url_usable('/a/b') is False
    """
    if url.endswith('/'):
        return True
    path, ext = splitext(url)
    return ext != ''
