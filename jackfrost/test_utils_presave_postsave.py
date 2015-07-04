# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from contextlib import contextmanager
from shutil import rmtree
from django.conf import settings
from django.test import override_settings
from django.utils.encoding import force_bytes
from jackfrost.models import URLWriter
import os
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db.models.signals import pre_save
from django.db.models.signals import post_save
from jackfrost.utils import build_page_for_obj
import pytest


@contextmanager
def tidying_signal(cls, signal):
    kwargs = {'receiver': build_page_for_obj,
              'sender': cls,
              'dispatch_uid': 'build_page_for_obj__pre_save'}
    signal.connect(**kwargs)
    yield
    signal.disconnect(**kwargs)


@pytest.mark.django_db
def test_using_as_presave():
    class UserPresaveProxy(get_user_model()):
        def get_absolute_url(self):
            return reverse('show_user', kwargs={'pk': self.pk})

        class Meta:
            proxy = True

    user = UserPresaveProxy.objects.create(username='whee')
    NEW_STATIC_ROOT = os.path.join(settings.BASE_DIR, 'test_collectstatic',
                                   'utils', 'using_as_presave')
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)

    # this is a bit hoop-jumpy ;/
    url = '%s/index.html' % user.get_absolute_url()[1:]
    writer = URLWriter(data=None)
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        storage = writer.storage
    with pytest.raises(IOError):
        storage.open(url)

    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        with tidying_signal(cls=UserPresaveProxy, signal=pre_save):
            user.save()

    url = '%s/index.html' % user.get_absolute_url()[1:]
    data = storage.open(url).readlines()
    assert data == [force_bytes(user.pk)]


@pytest.mark.django_db
def test_using_as_presave():
    class UserPresaveProxy(get_user_model()):
        def get_absolute_url(self):
            return reverse('show_user', kwargs={'pk': self.pk})

        class Meta:
            proxy = True

    user = UserPresaveProxy.objects.create(username='whee')
    NEW_STATIC_ROOT = os.path.join(settings.BASE_DIR, 'test_collectstatic',
                                   'utils', 'using_as_postsave')
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)

    # this is a bit hoop-jumpy ;/
    url = '%s/index.html' % user.get_absolute_url()[1:]
    writer = URLWriter(data=None)
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        storage = writer.storage
    with pytest.raises(IOError):
        storage.open(url)

    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        with tidying_signal(cls=UserPresaveProxy, signal=post_save):
            user.save()

    url = '%s/index.html' % user.get_absolute_url()[1:]
    data = storage.open(url).readlines()
    assert data == [force_bytes(user.pk)]
