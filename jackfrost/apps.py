# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from django.apps import AppConfig
from django.core.checks import registry


class JackFrostAppConfig(AppConfig):
    name = 'jackfrost'
    verbose_name = "Jack Frost"

    def ready(self):
        from .checks import check_renderers_setting
        registry.register(check_renderers_setting)
