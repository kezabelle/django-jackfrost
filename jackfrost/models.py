# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from collections import namedtuple
import logging
from mimetypes import guess_extension
# from django.core.urlresolvers import set_script_prefix
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import is_safe_url
# noinspection PyUnresolvedReferences
from django.utils.six.moves.urllib.parse import urlparse
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


__all__ = ['URLBuilder', 'URLCollector', 'ModelRenderer', 'SitemapRenderer',
           'MedusaRenderer']
logger = logging.getLogger(__name__)


# BuildRedirectResult = namedtuple('BuildRedirectResult', 'response storage_returned')  # noqa
BuildPageResult = namedtuple('BuildPageResult', 'response storage_returned')  # noqa
# BuildResult = namedtuple('BuildResult', 'built_pages client content_types storage_backend')  # noqa

class URLBuilder(object):
    """
    Given a list of URLs, presumably from a URLCollector, build them to files
    """
    __slots__ = ('urls', '_storage', '_client', '_content_types')

    def __init__(self, urls):
        self.urls = urls
        self._storage = None
        self._client = None
        self._content_types = None

    def get_content_types_mapping(self):
        return getattr(settings, 'JACKFROST_CONTENT_TYPES',
                       defaults.JACKFROST_CONTENT_TYPES)

    def get_target_filename(self, url, response):
        url = url.lstrip('/')
        if splitext(url)[1] == '':
            content_type = response['Content-Type']
            major = content_type.split(';', 1)[0]
            extension = self.content_types.get(
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

    @property
    def storage(self):
        if self._storage is None:
            self._storage = self.get_storage()
        return self._storage

    @property
    def client(self):
        if self._client is None:
            self._client = self.get_client()
        return self._client

    @property
    def content_types(self):
        if self._content_types is None:
            self._content_types = self.get_content_types_mapping()
        return self._content_types

    def write(self, name, content):
        if self.storage.exists(name=name):
            self.storage.delete(name=name)
        return self.storage.save(name=name, content=BytesIO(force_bytes(content)))  # noqa

    def build_redirect_page(self, url, final_url):
        urlparts = urlparse(url)
        url = urlparts.path

        if not is_safe_url(url):
            logger.error("Unable to generate a redirecting page for {url} "
                         "because Django says it's not safe".format(url=url))
            return BuildPageResult(response=None, storage_returned=None)

        try:
            result = render_to_string([
                normpath('jackfrost/{}/301.html'.format(final_url)),
                normpath('jackfrost/{}/301.html'.format(url)),
                'jackfrost/301.html',
                '301.html',
            ], {'this_url': url, 'next_url': final_url})
        except TemplateDoesNotExist:
            logger.error("Unable to generate a redirecting page for {url} "
                         "because there is no 301 template".format(url=url),
                         exc_info=1)
            return BuildPageResult(response=None, storage_returned=None)

        response = HttpResponse(content=result, content_type='text/html')
        filename = self.get_target_filename(url=url, response=response)
        stored = self.write(name=filename, content=result)
        built_page.send(sender=self.__class__,
                        builder=self,
                        url=url,
                        response=response,
                        filename=filename,
                        storage_result=stored)

        return BuildPageResult(response=response, storage_returned=stored)

    def build_error_page(self, error):
        try:
            result = render_to_string([
                'jackfrost/{error!s}.html'.format(error=error),
                '{error!s}.html'.format(error=error),
            ], {'request_path': None})
        except TemplateDoesNotExist:
            logger.error("Unable to generate a {error!s} page".format(error=error),  # noqa
                         exc_info=1)
            return BuildPageResult(response=None, storage_returned=None)
        else:
            response = HttpResponse(content=result)
            filename = self.get_target_filename(
                url='{error!s}.html'.format(error=error),
                response=response)
            stored = self.write(name=filename, content=result)
            built_page.send(sender=self.__class__,
                            builder=self,
                            url=None,
                            response=response,
                            filename=filename,
                            storage_result=stored)
            return BuildPageResult(response=response, storage_returned=stored)

    def build_page(self, url, url_index=None):
        resp = self.client.get(url, follow=True)
        status = resp.status_code
        stored = None
        if status == 200:
            # calculate changed URL and redirects if necessary
            if hasattr(resp, 'redirect_chain') and resp.redirect_chain:
                previous_pages = resp.redirect_chain[:]
                previous_pages.insert(0, (url, 301))  # hack to put in *this* url.
                final_url = previous_pages.pop()[0]
                urlparts = urlparse(final_url)
                url = urlparts.path
                for previous_page, previous_status in previous_pages:
                    self.build_redirect_page(url=previous_page,
                                             final_url=url)

            filename = self.get_target_filename(url=url, response=resp)
            if resp.streaming is True:
                response_content = b''.join(resp.streaming_content)
            else:
                response_content = resp.content
            stored = self.write(name=filename, content=response_content)
            built_page.send(sender=self.__class__,
                            builder=self,
                            url=url,
                            response=resp,
                            filename=filename,
                            storage_result=stored)
        return BuildPageResult(response=resp, storage_returned=stored)

    def build(self):
        builder_started.send(sender=self.__class__, builder=self)
        for idx, url in enumerate(self.urls, start=0):
            yield self.build_page(url=url, url_index=idx)
        for error in (401, 403, 404, 500):
            yield self.build_error_page(error=error)
        builder_finished.send(sender=self.__class__, builder=self)

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
        # TODO: figure out prefix necessities
        # url_prefix = getattr(settings, 'JACKFROST_SCRIPT_PREFIX', None)
        # if url_prefix is not None:
        #     set_script_prefix(url_prefix)
        self.renderers = frozenset(self.get_renderers(renderers=renderers))

    def __repr__(self):
        return '<%(mod)s.%(cls)s renderers=%(renderers)r>' % {
            'mod': self.__module__,
            'cls': self.__class__.__name__,
            'renderers': self.renderers,
        }

    def is_sitemap(self, cls):
        attrs = ('limit', 'protocol', 'items', 'get_urls')
        return all(hasattr(cls, x) for x in attrs)

    def is_medusa_renderer(self, cls):
        attrs = ('get_paths', 'generate')
        return all(hasattr(cls, x) for x in attrs)

    def is_feed(self, cls):
        attrs = ('get_feed', 'feed_type')
        return all(hasattr(cls, x) for x in attrs)

    def get_renderers(self, renderers=None):
        if renderers is None:
            try:
                renderers = settings.JACKFROST_RENDERERS
            except AttributeError:
                raise ImproperlyConfigured(
                    "You have not set `JACKFROST_RENDERERS` in your "
                    "project's settings")
        for renderer in renderers:
            if isinstance(renderer, six.string_types):
                renderer_cls = import_string(renderer)
            else:
                renderer_cls = renderer

            if self.is_sitemap(cls=renderer_cls):
                renderer_cls = SitemapRenderer(cls=renderer_cls)
            elif self.is_medusa_renderer(cls=renderer_cls):
                renderer_cls = MedusaRenderer(cls=renderer_cls)
            elif self.is_feed(cls=renderer_cls):
                renderer_cls = FeedRenderer(cls=renderer_cls)
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
        return self._get_urls()

    def __call__(self):
        return frozenset(self.get_urls())


class SitemapRenderer(object):
    """
    Given a standard Django Sitemap class, this exposes enough functionality
    to be a renderer of the URLs represented by the Sitemap's location() method.
    """
    __slots__ = ('sitemap_cls',)

    def __init__(self, cls):
        self.sitemap_cls = cls

    def __repr__(self):
        return '<%(mod)s.%(cls)s sitemap_cls=%(medusa)r>' % {
            'mod': self.__module__,
            'cls': self.__class__.__name__,
            'medusa': self.sitemap_cls,
        }

    def get_urls(self):
        sitemap = self.sitemap_cls()
        for page in sitemap.paginator.page_range:
            for result in sitemap.get_urls(page=page):
                if 'location' in result:
                    urlparts = urlparse(result['location'])
                    url = urlparts.path
                    yield url

    def __call__(self):
        return frozenset(self.get_urls())


class MedusaRenderer(object):
    __slots__ = ('medusa_cls',)

    def __init__(self, cls):
        self.medusa_cls = cls

    def __repr__(self):
        return '<%(mod)s.%(cls)s medusa_cls=%(medusa)r>' % {
            'mod': self.__module__,
            'cls': self.__class__.__name__,
            'medusa': self.medusa_cls,
        }

    def get_urls(self):
        return self.medusa_cls().get_paths()

    def __call__(self):
        return frozenset(self.get_urls())


class FeedRenderer(object):
    __slots__ = ('feed_cls',)

    def __init__(self, cls):
        self.feed_cls = cls

    def __repr__(self):
        return '<%(mod)s.%(cls)s feed_cls=%(medusa)r>' % {
            'mod': self.__module__,
            'cls': self.__class__.__name__,
            'medusa': self.feed_cls,
        }

    def get_urls(self):
        feed = self.feed_cls()
        # I have *NO* understanding of why the attribute has been renamed
        # ... what magic is happening here?
        for item in feed._Feed__get_dynamic_attr('items', None):
            yield feed._Feed__get_dynamic_attr('item_link', item)

    def __call__(self):
        return frozenset(self.get_urls())


