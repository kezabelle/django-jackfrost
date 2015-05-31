# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from django.conf import settings
import os
from shutil import rmtree
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.utils import override_settings
from jackfrost import defaults
from jackfrost.models import URLBuilder
import pytest


def setup_module(module):
    """
    Removes everything in our static folder between tests,
    so that we get false positives
    """
    builder = URLBuilder(urls=())
    NEW_STATIC_ROOT = os.path.join(settings.STATIC_ROOT, 'urlbuilder')
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        our_path = builder.storage.path('')
    assert our_path.startswith(settings.STATIC_ROOT) is True
    assert our_path.startswith(settings.BASE_DIR) is True
    # As this happens on every test, it will sometimes raise
    # OSError because collectstatic/jackfrost no longer exists.
    # We just ignore it and hope for the best ...
    rmtree(path=our_path, ignore_errors=True)



def test_get_content_types_mapping():
    builder = URLBuilder(urls=())
    assert builder.get_content_types_mapping() == defaults.JACKFROST_CONTENT_TYPES


def test_get_content_types_mapping_overrides():
    builder = URLBuilder(urls=())
    with override_settings(JACKFROST_CONTENT_TYPES={}):
        assert builder.get_content_types_mapping() == {}


def test_target_filename_without_extension():
    builder = URLBuilder(urls=())
    resp = {'Content-Type': 'text/html; charset=utf-8'}
    assert builder.get_target_filename(
        url='/a/b/c', response=resp) == 'jackfrost/a/b/c/index.html'


def test_target_filename_without_extension_other_type():
    builder = URLBuilder(urls=())
    resp = {'Content-Type': 'application/javascript'}
    assert builder.get_target_filename(
        url='/a/b/c/', response=resp) == 'jackfrost/a/b/c/index.js'


def test_target_filename_with_extension_already():
    builder = URLBuilder(urls=())
    resp = {'Content-Type': None}
    assert builder.get_target_filename(
        url='/a/b/c/test.js', response=resp) == 'jackfrost/a/b/c/test.js'


def test_get_client():
    builder = URLBuilder(urls=())
    assert isinstance(builder.get_client(), Client) is True


def test_get_storage():
    builder = URLBuilder(urls=())
    assert isinstance(builder.get_storage(), StaticFilesStorage) is True


def test_build():
    builder = URLBuilder(urls=(
        reverse('content_a'),
        reverse('content_b'),
    ))
    output = builder.build()
    files_saved = []
    for built in output:
        files_saved.append(built.storage_returned)
    sorted_files_saved = sorted(files_saved)
    assert sorted_files_saved == [
        'jackfrost/401.html',  # error page worked!
        'jackfrost/403.html',  # error page worked!
        'jackfrost/404.html',  # error page worked!
        'jackfrost/500.html',  # error page worked!
        'jackfrost/content/a/b/index.html',
        'jackfrost/content/a/index.html'
    ]
    storage = builder.storage
    assert storage.open(sorted_files_saved[-2]).readlines() == ['content_b']
    assert storage.open(sorted_files_saved[-1]).readlines() == ['content_a']
    # remove(storage)



def test_build_page():
    builder = URLBuilder(urls=())
    NEW_STATIC_ROOT = os.path.join(settings.STATIC_ROOT, 'urlbuilder', 'build_page')
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        storage = builder.storage
    output = builder.build_page(url=reverse('content_b'))
    assert output.response.status_code == 200
    assert output.storage_returned == 'jackfrost/content/a/b/index.html'
    assert storage.open(output.storage_returned).readlines() == ['content_b']
    # remove(storage)


def test_build_page_includes_redirections():
    builder = URLBuilder(urls=())
    NEW_STATIC_ROOT = os.path.join(settings.STATIC_ROOT, 'urlbuilder',
                                   'build_page_includes_redirections')
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        storage = builder.storage

    with pytest.raises(IOError):
        storage.open('jackfrost/r/a/index.html')
    with pytest.raises(IOError):
        storage.open('jackfrost/r/a_b/index.html')

    builder.build_page(url=reverse('redirect_a'))

    # redirects happened ...
    redirect_code = '<meta http-equiv="refresh" content="3; url={next}">'.format(
        next=reverse('content_b'),
    )
    redirect1 = storage.open('jackfrost/r/a/index.html').read()
    redirect2 = storage.open('jackfrost/r/a_b/index.html').read()
    assert redirect_code in redirect1
    assert redirect_code in redirect2
    # remove(storage)
