# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
import pytest
import django
from django.test.utils import override_settings

pytestmark = pytest.mark.xfail(django.VERSION[:2] < (1,7), reason="requires Django 1.7 to use the checks framework")  # noqa


@override_settings()
def test_missing_setting():
    from django.apps import apps
    from django.core.checks import WARNING
    from django.conf import settings
    del settings.JACKFROST_RENDERERS
    from jackfrost.checks import check_renderers_setting
    appconfigs = apps.get_app_configs()
    output = check_renderers_setting(appconfigs)[0]
    assert output.id == 'jackfrost.W001'
    assert output.level == WARNING


@override_settings(JACKFROST_RENDERERS="test.path")
def test_setting_is_string():
    """
    This is bad: ('test.test.test')
    this is good: ('test.test.test',)
    """
    from django.apps import apps
    from django.core.checks import ERROR
    from jackfrost.checks import check_renderers_setting
    appconfigs = apps.get_app_configs()
    output = check_renderers_setting(appconfigs)[0]
    assert output.id == 'jackfrost.E001'
    assert output.level == ERROR


@override_settings(JACKFROST_RENDERERS=["test.path"])
def test_setting_is_invalid_path():
    from django.apps import apps
    from django.core.checks import ERROR
    from jackfrost.checks import check_renderers_setting
    appconfigs = apps.get_app_configs()
    output = check_renderers_setting(appconfigs)[0]
    assert output.id == 'jackfrost.E002'
    assert output.level == ERROR
    assert output.msg == "Unable to import test.path"


@override_settings(JACKFROST_RENDERERS=[1])
def test_setting_is_not_a_string_to_import():
    from django.apps import apps
    from jackfrost.checks import check_renderers_setting
    appconfigs = apps.get_app_configs()
    output = check_renderers_setting(appconfigs)
    assert output == []
