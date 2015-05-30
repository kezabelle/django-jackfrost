# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from collections import namedtuple
import logging
from mimetypes import guess_extension
# from django.template import TemplateDoesNotExist
# from django.template.loader import render_to_string
# from django.utils.http import is_safe_url
from django.utils.six import BytesIO
from jackfrost.signals import builder_started, builder_finished, built_page
from os.path import splitext, join
try:
    from django.utils.module_loading import import_string
except ImportError:  # pragma: no cover
    from django.utils.module_loading import import_by_path as import_string
from django.conf import settings
from django.core.paginator import Paginator
from django.test.client import Client
from django.utils import six
from jackfrost import defaults
from posixpath import normpath
# from django.utils.six.moves.urllib.parse import urlparse


__all__ = ['URLBuilder', 'URLCollector', 'ModelRenderer']
logger = logging.getLogger(__name__)


BuildRedirectResult = namedtuple('BuildRedirectResult', 'response content storage_returned')  # noqa
BuildPageResult = namedtuple('BuildPageResult', 'response redirects storage_returned')  # noqa
BuildResult = namedtuple('BuildResult', 'built_pages client content_types storage_backend')  # noqa

class URLBuilder(object):
    """
    Given a list of URLs, presumably from a URLCollector, build them to files
    """
    __slots__ = ('urls')

    def __init__(self, urls):
        self.urls = urls

    def get_content_types_mapping(self):
        return getattr(settings, 'JACKFROST_CONTENT_TYPES',
                       defaults.JACKFROST_CONTENT_TYPES)

    def get_target_filename(self, url, response, content_types):
        url = url.lstrip('/')
        if splitext(url)[1] == '':
            content_type = response['Content-Type']
            major = content_type.split(';', 1)[0]
            extension = content_types.get(
                major, guess_extension(major, strict=False))
            filename = '{path}/{file}{ext}'.format(path=url, file='index',
                                                   ext=extension)
        else:
            filename = url
        return normpath(join('jackfrost', filename))

    def get_client(self):
        return Client()

    def get_storage(self):
        storage = getattr(settings, 'JACKFROST_STORAGE',
                          defaults.JACKFROST_STORAGE)
        kwargs = getattr(settings, 'JACKFROST_STORAGE_KWARGS',
                          defaults.JACKFROST_STORAGE_KWARGS)
        storage_cls = import_string(storage)
        return storage_cls(**kwargs)

    def write(self, name, content, storage):
        if storage.exists(name=name):
            storage.delete(name=name)
        return storage.save(name=name, content=BytesIO(content))
    #
    # def build_redirect_page(self, url, final_url, response, storage, content_types):
    #     urlparts = urlparse(url)
    #     url = urlparts.path
    #     if not is_safe_url(url):
    #         logger.error("Unable to generate a redirecting page for {url} "
    #                      "because Django says it's not safe".format(url=url))
    #         return BuildRedirectResult(response=None, content=None,
    #                                    storage_returned=None)
    #     try:
    #         result = render_to_string(template_name=[
    #             normpath('jackfrost/{}/301.html'.format(final_url)),
    #             normpath('jackfrost/{}/301.html'.format(url)),
    #             'jackfrost/301.html',
    #             '301.html',
    #         ], context={'this_url': url, 'next_url': final_url})
    #     except TemplateDoesNotExist as e:
    #         logger.error("Unable to generate a redirecting page for {url} "
    #                      "because there is no 301 template".format(url=url),
    #                      exc_info=1)
    #         return BuildRedirectResult(response=None, content=None,
    #                                    storage_returned=None)
    #     filename = self.get_target_filename(url=url, response=response,
    #                                         content_types=content_types)
    #     stored = self.write(name=filename, content=BytesIO(result),
    #                         storage=storage)
    #     built_page.send(sender=self.__class__,
    #                     builder=self,
    #                     url=url,
    #                     response=response,
    #                     filename=filename,
    #                     storage_backend=storage,
    #                     storage_result=stored)
    #     return BuildRedirectResult(response=response, content=result,
    #                                storage_returned=stored)

    def build_page(self, url, client, storage, content_types, url_index=None):
        resp = client.get(url, follow=True)
        stored = None
        redirects = []
        if resp.status_code == 200:
            # if hasattr(resp, 'redirect_chain') and resp.redirect_chain:
            #     import pdb; pdb.set_trace()
            #     for r_url, status in resp.redirect_chain:
            #         redirects.append(
            #             self.build_redirect_page(url=r_url, final_url=url,
            #                                      response=resp,
            #                                      storage=storage,
            #                                    content_types=content_types))
            #     logger.debug("{url!s} went through a number of redirects")

            filename = self.get_target_filename(url=url, response=resp,
                                                content_types=content_types)
            stored = self.write(name=filename, content=resp.content,
                                storage=storage)
            built_page.send(sender=self.__class__,
                            builder=self,
                            url=url,
                            response=resp,
                            filename=filename,
                            storage_backend=storage,
                            storage_result=stored)
        return BuildPageResult(response=resp, redirects=tuple(redirects),
                               storage_returned=stored)

    def build(self):
        builder_started.send(sender=self.__class__, builder=self)
        client = self.get_client()
        content_types = self.get_content_types_mapping()
        storage = self.get_storage()
        built = set()
        for idx, url in enumerate(self.urls, start=0):
            built.add(self.build_page(url=url, client=client, storage=storage,
                                      content_types=content_types,
                                      url_index=idx))
        builder_finished.send(sender=self.__class__, builder=self)
        return BuildResult(built_pages=built, client=client,
                           content_types=content_types,
                           storage_backend=storage)

    def __call__(self):
        return self.build()


class URLCollector(object):
    """
    >>> x = URLCollector(renderers=['a.b.C', DEF])
    >>> urls = x()
    ('/', '/a/b/', '/c/')
    """
    __slots__ = ('renderers',)

    def __init__(self, renderers=None):
        self.renderers = frozenset(self.get_renderers(renderers=renderers))

    def get_renderers(self, renderers=None):
        if renderers is None:
            from django.conf import settings
            renderers = settings.JACKFROST_RENDERERS
        for renderer in renderers:
            if isinstance(renderer, six.text_type):
                renderer_cls = import_string(renderer)
            else:
                renderer_cls = renderer
            yield renderer_cls

    def get_urls(self):
        urls = set()
        for renderer in self.renderers:
            _cls_or_func_result = renderer()
            # if it was a class, we still need to call __call__
            if callable(_cls_or_func_result):
                _cls_or_func_result = _cls_or_func_result()
            # ensure it's evaluated, incase the renderer is a generator which
            # doesn't wrap itself ...
            for url in _cls_or_func_result:
                urls.add(url)
        return urls

    def __call__(self):
        return self.get_urls()


# Originally: https://gist.github.com/kezabelle/6683315
class ChunkingPaginator(Paginator):
    def chunked_objects(self):
        for page in self.page_range:
            for obj in self.page(page):
                yield obj


class ModelRenderer(object):
    """
    If you just want to render a queryset out, and the model has
    appropriate methods, just subclass this ...
    """
    __slots__ = ()

    def get_model(self):
        raise NotImplementedError("You need to override this ")

    def get_queryset(self):
        return self.get_model().objects.all()

    def get_paginated_queryset(self):
        """
        By default we avoid consuming too much of the database at once, even
        though it means more queries overall.
        You can just replace this with
        return self.get_queryset().iterator() or something if you want.
        """
        return ChunkingPaginator(self.get_queryset(), 50).chunked_objects()

    def _get_urls(self):
        for obj in self.get_paginated_queryset():
            # on the off-chance the app knows it may want to not build things...
            if hasattr(obj, 'jackfrost_can_build'):
                if obj.jackfrost_can_build() is False:
                    continue

            if hasattr(obj, 'jackfrost_absolute_url'):
                # on the off-chance an app needs to ship specific URLs for us...
                logger.debug("{obj!r} had `jackfrost_absolute_url` method")
                yield obj.jackfrost_absolute_url()
            elif hasattr(obj, 'get_absolute_url'):
                yield obj.get_absolute_url()
            else:
                logger.warning("{obj!r} has no `get_absolute_url` method")
            if hasattr(obj, 'get_list_url'):
                yield obj.get_list_url()

    def get_urls(self):
        return frozenset(self._get_urls())

    def __call__(self):
        return self.get_urls()
