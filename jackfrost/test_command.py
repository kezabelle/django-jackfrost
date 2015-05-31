# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from shutil import rmtree
import os
from django.conf import settings
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from jackfrost.models import URLBuilder
import pytest


def setup_module(module):
    """
    Removes everything in our static folder between tests,
    so that we get false positives
    """
    builder = URLBuilder(urls=())
    NEW_STATIC_ROOT = os.path.join(settings.STATIC_ROOT, 'collectstaticsite')
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        our_path = builder.storage.path('')
    assert our_path.startswith(settings.STATIC_ROOT) is True
    assert our_path.startswith(settings.BASE_DIR) is True
    # As this happens on every test, it will sometimes raise
    # OSError because collectstatic/jackfrost no longer exists.
    # We just ignore it and hope for the best ...
    rmtree(path=our_path, ignore_errors=True)


def remove(storage):
    """
    Removes everything in our static folder between tests,
    so that we get false positives
    """
    our_path = storage.path('')
    from django.conf import settings
    assert our_path.startswith(settings.STATIC_ROOT) is True
    assert our_path.startswith(settings.BASE_DIR) is True
    # As this happens on every test, it will sometimes raise
    # OSError because collectstatic/jackfrost no longer exists.
    # We just ignore it and hope for the best ...
    rmtree(path=our_path, ignore_errors=True)


class DummyRenderer():
    def __call__(self):
        yield reverse('redirect_a')
        yield reverse('content_a')


def test_collectstaticsite_goes_ok():
    builder = URLBuilder(urls=())
    NEW_STATIC_ROOT = os.path.join(settings.STATIC_ROOT, 'collectstaticsite',
                                   'goes_ok')
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        storage = builder.storage

    with pytest.raises(IOError):
        storage.open('jackfrost/r/a/index.html')
    with pytest.raises(IOError):
        storage.open('jackfrost/r/a_b/index.html')
    with pytest.raises(IOError):
        storage.open('jackfrost/content/a/index.html')
    with pytest.raises(IOError):
        storage.open('jackfrost/content/a/b/index.html')

    with override_settings(JACKFROST_RENDERERS=[DummyRenderer], STATIC_ROOT=NEW_STATIC_ROOT):
        output = call_command('collectstaticsite', interactive=False)
    assert output == None

    # redirects happened ...
    redirect_code = '<meta http-equiv="refresh" content="3; url={next}">'.format(
        next=reverse('content_b'),
    )
    redirect1 = storage.open('jackfrost/r/a/index.html').read()
    redirect2 = storage.open('jackfrost/r/a_b/index.html').read()
    assert redirect_code in redirect1
    assert redirect_code in redirect2
    assert storage.open('jackfrost/content/a/index.html').readlines() == ['content_a']  # noqa
    assert storage.open('jackfrost/content/a/b/index.html').readlines() == ['content_b']  # noqa
