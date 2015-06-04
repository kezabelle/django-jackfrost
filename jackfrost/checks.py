# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from django.core.checks import Warning
from django.core.checks import Error
from django.utils.six import string_types
try:
    from django.utils.module_loading import import_string
except ImportError:  # pragma: no cover
    from django.utils.module_loading import import_by_path as import_string


def check_renderers_setting(app_configs, **kwargs):
    from django.conf import settings
    errors = []
    if not hasattr(settings, 'JACKFROST_RENDERERS'):
        errors.append(Warning(
            msg="You don't have any renderers defined",
            hint="Set JACKFROST_RENDERERS to a tuple of renderers",
            id='jackfrost.W001',
        ))
    elif isinstance(settings.JACKFROST_RENDERERS, string_types):
        errors.append(Error(
            msg="JACKFROST_RENDERERS is a string, not an iterable",
            hint="You probably missed the trailing comma from a tuple...",
            id='jackfrost.E001'
        ))
    else:
        for renderer in settings.JACKFROST_RENDERERS:
            if isinstance(renderer, string_types):
                try:
                    import_string(renderer)
                except ImportError:
                    errors.append(Error(
                        msg="Unable to import %s" % renderer,
                        hint="Double check this is the dotted path to a "
                             "renderer instance",
                        id='jackfrost.E002',
                    ))
    return errors
