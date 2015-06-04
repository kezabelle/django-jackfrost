# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from jackfrost.models import URLCollector
import pytest


class DummyRenderer():
    def __call__(self):
        yield '/a/'
        yield '/b/'
        yield '/c/'


class DummyRenderer2():
    def __call__(self):
        yield '/x/'
        yield '/y/'
        yield '/z/'


def dummy_renderer_3():
    return ['/fromfunc/']


def test_settings_error_if_not_set():
    with pytest.raises(ImproperlyConfigured):
        URLCollector(renderers=None)


def test_settings_ok_when_set():
    with override_settings(JACKFROST_RENDERERS=()):
        URLCollector(renderers=None)


def test_renderers_override_defaults():
    with override_settings(JACKFROST_RENDERERS=('jackfrost.test_urlcollector.DummyRenderer',)):  # noqa
        collector = URLCollector(renderers=None)
    assert collector.renderers == frozenset([DummyRenderer])


def test_renderers_override_defaults_with_class():
    with override_settings(JACKFROST_RENDERERS=(DummyRenderer,)):
        collector = URLCollector(renderers=None)
    assert collector.renderers == frozenset([DummyRenderer])


def test_renderers_provided_directly():
    collector = URLCollector(renderers=(DummyRenderer,))
    assert collector.renderers == frozenset([DummyRenderer])


def test_renderers_provided_directly_as_string():
    collector = URLCollector(renderers=('jackfrost.test_urlcollector.DummyRenderer',))  # noqa
    assert collector.renderers == frozenset([DummyRenderer])


def test_get_urls():
    collector = URLCollector(renderers=(DummyRenderer, DummyRenderer2,
                                        dummy_renderer_3))
    assert frozenset(collector.get_urls()) == frozenset(['/a/', '/b/', '/c/',
                                                         '/fromfunc/',
                                                         '/x/', '/y/', '/z/'])

def test_call_calls_get_urls():
    collector = URLCollector(renderers=(DummyRenderer, DummyRenderer2,
                                        dummy_renderer_3))
    assert frozenset(collector()) == frozenset(['/a/', '/b/', '/c/',
                                                 '/fromfunc/',
                                                 '/x/', '/y/', '/z/'])
