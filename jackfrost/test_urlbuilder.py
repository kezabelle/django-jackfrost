# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from django.conf import settings
from django.utils.encoding import force_bytes
import os
from shutil import rmtree
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.utils import override_settings
from jackfrost import defaults
from jackfrost.models import URLBuilder
from jackfrost.defaults import SubfolderStaticFilesStorage
import pytest


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
        url='/a/b/c', response=resp) == 'a/b/c/index.html'


def test_target_filename_without_extension_other_type():
    builder = URLBuilder(urls=())
    resp = {'Content-Type': 'application/javascript'}
    assert builder.get_target_filename(
        url='/a/b/c/', response=resp) == 'a/b/c/index.js'


def test_target_filename_with_extension_already():
    builder = URLBuilder(urls=())
    resp = {'Content-Type': None}
    assert builder.get_target_filename(
        url='/a/b/c/test.js', response=resp) == 'a/b/c/test.js'


def test_get_client():
    builder = URLBuilder(urls=())
    assert isinstance(builder.get_client(), Client) is True


def test_get_storage():
    builder = URLBuilder(urls=())
    assert isinstance(builder.get_storage(), SubfolderStaticFilesStorage) is True
    assert builder.get_storage().location == os.path.join(settings.BASE_DIR,
                                                          'test_collectstatic',
                                                          'jackfrost')


def test_build():
    builder = URLBuilder(urls=(
        reverse('content_a'),
        reverse('content_b'),
    ))
    NEW_STATIC_ROOT = os.path.join(settings.BASE_DIR, 'test_collectstatic',
                                   'urlbuilder', 'build')
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        storage = builder.storage
    output = builder.build()
    files_saved = []
    for built in output:
        files_saved.append(built.storage_returned)
    sorted_files_saved = sorted(files_saved)
    assert sorted_files_saved == [
        '401.html',  # error page worked!
        '403.html',  # error page worked!
        '404.html',  # error page worked!
        '500.html',  # error page worked!
        'content/a/b/index.html',
        'content/a/index.html'
    ]
    assert storage.open(sorted_files_saved[-2]).readlines() == [b'content_b']
    assert storage.open(sorted_files_saved[-1]).readlines() == [b'content_a']
    # remove(storage)



def test_build_page():
    builder = URLBuilder(urls=())
    NEW_STATIC_ROOT = os.path.join(settings.BASE_DIR, 'test_collectstatic',
                                   'urlbuilder', 'build_page')
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        storage = builder.storage
    output = builder.build_page(url=reverse('content_b'))
    assert output.response.status_code == 200
    assert output.storage_returned == 'content/a/b/index.html'
    assert storage.open(output.storage_returned).readlines() == [b'content_b']


def test_build_page_includes_redirections():
    builder = URLBuilder(urls=())
    NEW_STATIC_ROOT = os.path.join(settings.BASE_DIR, 'test_collectstatic',
                                   'urlbuilder',
                                   'build_page_includes_redirections')
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        storage = builder.storage

    with pytest.raises(IOError):
        storage.open('r/a/index.html')
    with pytest.raises(IOError):
        storage.open('r/a_b/index.html')

    builder.build_page(url=reverse('redirect_a'))

    # redirects happened ...
    redirect_code = force_bytes('<meta http-equiv="refresh" content="3; '
                                'url={next}">'.format(next=reverse('content_b')))
    redirect1 = storage.open('r/a/index.html').read()
    redirect2 = storage.open('r/a_b/index.html').read()
    assert redirect_code in redirect1
    assert redirect_code in redirect2


def test_build_page_streaming_response():
    builder = URLBuilder(urls=())
    NEW_STATIC_ROOT = os.path.join(settings.BASE_DIR, 'test_collectstatic',
                                   'urlbuilder', 'streaming_response')
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        storage = builder.storage
    output = builder.build_page(url=reverse('streamable'))
    assert output.response.status_code == 200
    assert output.storage_returned == 'streamable/index.html'
    assert storage.open(output.storage_returned).readlines() == [b"helloI'mastream"]
