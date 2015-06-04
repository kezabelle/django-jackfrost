# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from django.apps import AppConfig


class JackFrostAppConfig(AppConfig):
    name = 'jackfrost'
    verbose_name = "Jack Frost"

    def ready(self):
        from .checks import *  # noqa
