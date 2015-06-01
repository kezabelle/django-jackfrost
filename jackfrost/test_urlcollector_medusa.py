# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from django.contrib.auth import get_user_model
from jackfrost.models import URLCollector, MedusaRenderer
import pytest


def test_medusa_renderer_repr():
    assert repr(MedusaRenderer(cls=1)) == '<jackfrost.models.MedusaRenderer medusa_cls=1>'


@pytest.mark.django_db
def test_medusa_renderer_support():

    class UserMedusaProxy(get_user_model()):
        def get_absolute_url(self):
            return '/test/medusa/{}/'.format(self.pk)

        class Meta:
            proxy = True

    class MedusaLikeRenderer(object):
        def generate(self):
            return True

        def get_paths(self):
            return [x.get_absolute_url() for x in UserMedusaProxy.objects.all()]

    users = [get_user_model().objects.create(username='medusa{}'.format(x))
             for x in range(1, 5)]
    user_pks = [u.pk for u in users]
    users_urls = [up.get_absolute_url()
                  for up in UserMedusaProxy.objects.filter(pk__in=user_pks)]
    collector = URLCollector(renderers=(MedusaLikeRenderer,))
    assert frozenset(collector()) == frozenset(users_urls)
