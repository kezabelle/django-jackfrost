# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from django.contrib import admin
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.test.utils import override_settings
from django.utils.encoding import force_bytes, force_text
from django.contrib.messages.middleware import MessageMiddleware
from jackfrost.actions import build_selected
from jackfrost.models import URLWriter
import os
from shutil import rmtree
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
import pytest


@pytest.mark.django_db
def test_actions_build_selected_get():
    class UserActionGETProxy(get_user_model()):
        def get_absolute_url(self):
            return reverse('show_user', kwargs={'pk': self.pk})

        class Meta:
            proxy = True

    user = UserActionGETProxy.objects.create(username='whee', is_superuser=True)

    madmin = admin.site._registry[get_user_model()]
    request = RequestFactory().get('/')
    request.user = user
    SessionMiddleware().process_request(request=request)
    MessageMiddleware().process_request(request=request)
    do_stuff = build_selected(modeladmin=madmin, request=request,
                              queryset=UserActionGETProxy.objects.all())
    assert force_text(do_stuff.context_data['title']) == 'Are you sure?'
    assert do_stuff.context_data['buildable_objects'] == {user.get_absolute_url()}
    assert set(do_stuff.context_data['queryset']) == set(UserActionGETProxy.objects.all())  # noqa
    assert do_stuff.context_data['queryset_count'] == 1
    assert do_stuff.context_data['buildable_objects_count'] == 1


@pytest.mark.django_db
def test_actions_build_selected_post():
    class UserActionPOSTProxy(get_user_model()):
        def get_absolute_url(self):
            return reverse('show_user', kwargs={'pk': self.pk})

        class Meta:
            proxy = True

    user = UserActionPOSTProxy.objects.create(username='whee', is_superuser=True)
    NEW_STATIC_ROOT = os.path.join(settings.BASE_DIR, 'test_collectstatic',
                                   'actions', 'build_selected_post')
    rmtree(path=NEW_STATIC_ROOT, ignore_errors=True)

    # this is a bit hoop-jumpy ;/
    url = '%s/index.html' % user.get_absolute_url()[1:]
    writer = URLWriter(data=None)
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):
        storage = writer.storage
    with pytest.raises(IOError):
        storage.open(url)

    madmin = admin.site._registry[get_user_model()]
    request = RequestFactory().post('/', data={'post': '1'})
    request.user = user
    SessionMiddleware().process_request(request=request)
    MessageMiddleware().process_request(request=request)
    with override_settings(STATIC_ROOT=NEW_STATIC_ROOT):

        do_stuff = build_selected(modeladmin=madmin, request=request,
                                  queryset=UserActionPOSTProxy.objects.all())
        assert do_stuff is None

    url = '%s/index.html' % user.get_absolute_url()[1:]
    data = storage.open(url).readlines()
    assert data == [force_bytes(user.pk)]
