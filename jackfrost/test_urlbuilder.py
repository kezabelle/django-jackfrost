# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.utils import override_settings
from jackfrost import defaults
from jackfrost.models import URLBuilder


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
        url='/a/b/c', response=resp,
        content_types=defaults.JACKFROST_CONTENT_TYPES) == 'jackfrost/a/b/c/index.html'  # noqa


def test_target_filename_without_extension_other_type():
    builder = URLBuilder(urls=())
    resp = {'Content-Type': 'application/javascript'}
    assert builder.get_target_filename(
        url='/a/b/c/', response=resp,
        content_types=defaults.JACKFROST_CONTENT_TYPES) == 'jackfrost/a/b/c/index.js'  # noqa


def test_target_filename_with_extension_already():
    builder = URLBuilder(urls=())
    resp = {'Content-Type': None}
    assert builder.get_target_filename(
        url='/a/b/c/test.js', response=resp,
        content_types=defaults.JACKFROST_CONTENT_TYPES) == 'jackfrost/a/b/c/test.js'  # noqa


def test_get_client():
    builder = URLBuilder(urls=())
    assert isinstance(builder.get_client(), Client) is True


def test_get_storage():
    builder = URLBuilder(urls=())
    assert isinstance(builder.get_storage(), FileSystemStorage) is True


def test_build():
    builder = URLBuilder(urls=(
        reverse('content_a'),
        reverse('content_b'),
    ))
    output = builder.build()
    files_saved = []
    for built in output.built_pages:
        files_saved.append(built.storage_returned)
    sorted_files_saved = sorted(files_saved)
    assert sorted_files_saved == ['jackfrost/content/a/b/index.html',
                                  'jackfrost/content/a/index.html']
    storage = builder.get_storage()
    assert storage.open(sorted_files_saved[0]).readlines() == ['content_b']
    assert storage.open(sorted_files_saved[1]).readlines() == ['content_a']


def test_build_page():
    builder = URLBuilder(urls=())
    client = builder.get_client()
    content_types = builder.get_content_types_mapping()
    storage = builder.get_storage()
    output = builder.build_page(url=reverse('redirect_a'), client=client,
                                storage=storage, content_types=content_types)
    assert output.response.status_code == 200
    assert output.storage_returned == 'jackfrost/r/a/index.html'
    assert storage.open(output.storage_returned).readlines() == ['content_b']
