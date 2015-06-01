# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse
from django.http.response import StreamingHttpResponse
from django.http.response import HttpResponseRedirect


def streamer(request):
    return StreamingHttpResponse(['hello', "I'm", 'a', 'stream'])

def content_a(request):
    return HttpResponse('content_a')


def content_b(request):
    return HttpResponse('content_b')


def redirect_a(request):
    return HttpResponseRedirect(reverse('redirect_b'))



def redirect_b(request):
    return HttpResponseRedirect(reverse('content_b'))


urlpatterns = patterns('',
   url(r'^streamable/$', streamer, name='streamable'),
   url(r'^content/a/b/$', content_b, name='content_b'),
   url(r'^content/a/$', content_a, name='content_a'),
   url(r'^r/a/$', redirect_a, name='redirect_a'),
   url(r'^r/a_b/$', redirect_b, name='redirect_b'),
)
