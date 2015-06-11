# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from jackfrost.defaults import SubfolderStaticFilesStorage
import os
from shutil import rmtree
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from jackfrost.models import URLReader
from jackfrost.models import ReadResult
from jackfrost.models import URLWriter


def test_repr_short():
    reads = [ReadResult(url='/%d/' % x, filename=None, status=None, content=None)
             for x in range(2)]
    reader = URLWriter(data=reads)
    assert repr(reader) == '<jackfrost.models.URLWriter data=("/0/", "/1/")>'


def test_repr_long():
    reads = [ReadResult(url='/%d/' % x, filename=None, status=None, content=None)
             for x in range(4)]
    reader = URLWriter(data=reads)
    assert repr(reader) == '<jackfrost.models.URLWriter data=("/0/", "/1/", "/2/" ... 1 remaining)>'  # noqa


def test_get_storage():
    writer = URLWriter(data=None)
    assert isinstance(writer.storage, SubfolderStaticFilesStorage) is True
    assert writer.storage.location == os.path.join(settings.BASE_DIR,
                                                   'test_collectstatic',
                                                   'jackfrost')


def test_build():
    reader = URLReader(urls=(
        reverse('content_a'),
        reverse('content_b'),
    ))
    read_results = tuple(reader())
    NEW_STATIC_ROOT = os.path.join(settings.BASE_DIR, 'test_collectstatic',
                                   'urlwriter', 'build')
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)
    writer = URLWriter(data=read_results)
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        storage = writer.storage
    output = writer()
    files_saved = []
    for built in output:
        files_saved.append(built.storage_result)
    sorted_files_saved = sorted(files_saved)
    assert sorted_files_saved == [
        'content/a/b/index.html',
        'content/a/index.html'
    ]
    assert storage.open(sorted_files_saved[-2]).readlines() == [b'content_b']
    assert storage.open(sorted_files_saved[-1]).readlines() == [b'content_a']
    # remove(storage)



def test_write_single_item():
    reader = URLReader(urls=[reverse('content_b')])
    read_results = tuple(reader())
    writer = URLWriter(data=read_results)

    NEW_STATIC_ROOT = os.path.join(settings.BASE_DIR, 'test_collectstatic',
                                   'urlwriter', 'write_single_item')
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        storage = writer.storage

    output = writer.write(read_results[0])
    assert output.md5 == 'f8ee7c48dfd7f776b3d011950a5c02d1'
    assert output.created is True
    assert output.modified is True
    assert output.name == 'content/a/b/index.html'
    assert storage.open(output.name).readlines() == [b'content_b']
