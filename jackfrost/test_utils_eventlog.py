# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from contextlib import contextmanager
import django
from jackfrost.utils import eventlog_write
from jackfrost.signals import write_page
import pytest
from django.core.urlresolvers import reverse
pytestmark = pytest.mark.xfail(django.VERSION[:2] < (1,7),
                               reason="requires Django 1.7 to use the appconfig")  # noqa
from jackfrost.models import URLReader, URLWriter
from pinax.eventlog.models import Log


@contextmanager
def sortof_tidying_signal(signal):
    kwargs = {'receiver': eventlog_write,
              'dispatch_uid': 'pinax_eventlog_write'}
    signal.connect(**kwargs)
    try:
        yield
    finally:
        signal.disconnect(**kwargs)


@pytest.mark.django_db
def test_eventlog_fires():
    from django.test import modify_settings
    with modify_settings(INSTALLED_APPS={
        'remove': ['jackfrost'],
        'append': ['pinax.eventlog']
    }):
        reader = URLReader(urls=[reverse('content_b')])
        read_results = tuple(reader())
        writer = URLWriter(data=read_results)
        with sortof_tidying_signal(signal=write_page):
            output = writer.write(read_results[0])
        assert Log.objects.count() == 1
        logged = Log.objects.get()
        assert logged.action == 'URL "/content/a/b/" written'
        assert 'ReadResult' in logged.extra
        assert 'WriteResult' in logged.extra
        assert logged.extra['WriteResult']['md5'] == 'f8ee7c48dfd7f776b3d011950a5c02d1'

