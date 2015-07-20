# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from django.core.urlresolvers import reverse
from django.utils.encoding import force_bytes
from django.test.client import Client
from django.test.utils import override_settings
from jackfrost import defaults
from jackfrost.models import URLReader, ReaderError
import pytest


def test_get_content_types_mapping():
    reader = URLReader(urls=())
    assert reader.content_types == defaults.JACKFROST_CONTENT_TYPES


def test_repr_short():
    reader = URLReader(urls=('/a/', '/b/'))
    assert repr(reader) == '<jackfrost.models.URLReader urls=["/a/", "/b/"]>'


def test_repr_long():
    reader = URLReader(urls=('/a/', '/b/', '/c/', '/d/', '/e/'))
    assert repr(reader) == '<jackfrost.models.URLReader urls=["/a/", "/b/", "/c/" ... 2 remaining]>'  # noqa


def test_get_content_types_mapping_overrides():
    reader = URLReader(urls=())
    with override_settings(JACKFROST_CONTENT_TYPES={}):
        assert reader.content_types == {}


def test_target_filename_root_url():
    reader = URLReader(urls=())
    resp = {'Content-Type': 'text/html; charset=utf-8'}
    assert reader.get_target_filename(url='/', response=resp) == 'index.html'


def test_target_filename_root_file():
    reader = URLReader(urls=())
    resp = {'Content-Type': 'text/html; charset=utf-8'}
    assert reader.get_target_filename(url='/index.json', response=resp) == 'index.json'


def test_target_filename_root_file_without_extension():
    reader = URLReader(urls=())
    resp = {'Content-Type': 'application/javascript; charset=utf-8'}
    assert reader.get_target_filename(url='/testjson/', response=resp) == 'testjson/index.js'


def test_target_filename_without_extension_and_no_trailing_slash():
    reader = URLReader(urls=())
    resp = {'Content-Type': 'text/html; charset=utf-8'}
    with pytest.raises(ReaderError):
        reader.get_target_filename(url='/a/b/c', response=resp)


def test_target_filename_without_extension_other_type():
    reader = URLReader(urls=())
    resp = {'Content-Type': 'application/javascript'}
    assert reader.get_target_filename(
        url='/a/b/c/', response=resp) == 'a/b/c/index.js'


def test_target_filename_with_extension_already():
    reader = URLReader(urls=())
    resp = {'Content-Type': None}
    assert reader.get_target_filename(
        url='/a/b/c/test.js', response=resp) == 'a/b/c/test.js'


def test_target_filename_xmltype():
    reader = URLReader(urls=())
    resp = {'Content-Type': None}
    assert reader.get_target_filename(
        url='sitemap.xml', response=resp) == 'sitemap.xml'


def test_get_client():
    reader = URLReader(urls=())
    assert isinstance(reader.client, Client) is True


def test_streaming_response():
    reader = URLReader(urls=[reverse('streamable')])
    output = tuple(reader())[0]
    assert output.status == 200
    assert output.filename == 'streamable/index.html'
    assert output.content == b"helloI'mastream"


def test_build_page_includes_redirections():
    reader = URLReader(urls=())

    result = tuple(reader.build_page(url=reverse('redirect_a')))
    redirect_code = force_bytes('<meta http-equiv="refresh" content="3; '
                                'url={next}">'.format(next=reverse('content_b')))

    assert len(result) == 3
    first, second, third = result

    # first redirect, pointing to last thing ...
    assert first.status is None
    assert first.url == '/r/a/'
    assert first.filename == 'r/a/index.html'
    assert redirect_code in first.content

    # second redirect, also pointing to last thing.
    assert second.status is None
    assert second.url == '/r/a_b/'
    assert second.filename == 'r/a_b/index.html'
    assert redirect_code in second.content

    # the content itself ...
    assert third.status == 200
    assert third.url == '/content/a/b/'
    assert third.filename == 'content/a/b/index.html'
    assert third.content == b'content_b'
