django-jackfrost 0.2.1
======================

.. image:: https://travis-ci.org/kezabelle/django-jackfrost.svg?branch=master
  :target: https://travis-ci.org/kezabelle/django-jackfrost

Allows rendering Django views into a collection of static files.

`django-medusa`_ doesn't appear to be active anymore, and I didn't like the
restrictions on where it stored things.

This is my attempt at a static site renderer, instead leveraging the availability
of Django's `staticfiles`_ functionality to leave specifics to someone else :)
The theory is thus that you could choose a third party storage from, say,
`django-storages`_ and plug it into `jackfrost` and have things Just Work.

I don't actually know if that's true though.

Unlike `django-medusa`_, and the `Django`_ admin, there is no autodiscovery,
and no requirement that renderers go in a specific place.

Unlike `django-bakery`_, I have a documented license; AFAIK, `they don't`_ :(

Unlike either of them, ``django-jackfrost`` has never actually been used. But it
does have good test coverage, sooooo ...

TODO
====

- Figure out which ideas from `django-bakery`_ I'd like to approximate.

Dependencies
============

-  `Django`_
-  `pytest`_

Installing
==========

Something like this, with `pip`_ installed, I think::

    pip install git+https://github.com/kezabelle/django-jackfrost.git#egg=django-jackfrost


Put ``jackfrost`` into your ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        'django.contrib.auth',
        # ...
        'jackfrost',
        # ...
    )

which will enable the management command::

    python manage.py collectstaticsite --processes=N


Configuration & usage
---------------------

Set ``JACKFROST_STORAGE`` to whatever storage backend you'd like to use, in
your project's settings. By default, a subclass of
``django.contrib.staticfiles.storage.StaticFilesStorage`` which puts output into
a ``jackfrost`` directory will be used.

If your storage backend needs any arguments that can't be gleaned from individual
settings, you can set ``JACKFROST_STORAGE_KWARGS`` to a dictionary of
arguments to be used when instantiating the ``JACKFROST_STORAGE``


Selecting renderers
^^^^^^^^^^^^^^^^^^^

Add a ``JACKFROST_RENDERERS`` setting, which should be a list or tuple of
dotted paths to python classes or functions, much like ``MIDDLEWARE_CLASSES``,
``TEMPLATE_CONTEXT_PROCESSORS`` etc::

    JACKFROST_RENDERERS = (
        'myapp.renderers.MyModelRenderer',
        'my_other_app.utils.SomeOtherRenderer',
    )

In theory, I don't care whether your ``JACKFROST_RENDERERS`` are functions
or classes; if it's a class it must implement ``__call__``. Either way,
it should, when called, return a number of URL paths to be consumed.


Renderers for models
^^^^^^^^^^^^^^^^^^^^

If you have a model which has a ``get_absolute_url`` method, your renderer
can be as simple as::

    from jackfrost.models import ModelRenderer

    class MyModelRenderer(ModelRenderer):
        def get_model(self):
            return MyModel

If you need to customise the queryset, there is a ``get_queryset`` method
which can be replaced. There is also a ``get_urls`` method, if you need to
go totally off-reservation.


Reading from `sitemaps`_
^^^^^^^^^^^^^^^^^^^^^^^^

Giving ``jackfrost`` the dotted path to a standard `Django sitemap`_ as
one of the ``JACKFROST_RENDERERS`` should do the right thing, and get the
URLs out of the sitemap itself without you needing to do anything or write
a new renderer.


Reading from `django-medusa`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In theory, giving ``jackfrost`` the dotted path to a subclass of the `django-medusa`_
`BaseStaticSiteRenderer`_ should do the right thing, and get the URLs out of
the medusa renderer itself, without you doing anything. It will avoid going
through the medusa rendering process, instead it'll go through mine.


Reading from `Django RSS Feeds`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Giving ``jackfrost`` the dotted path to a subclass of a `Feed`_
should do the right thing, and get the URLs out by asking the `Feed`_ for the
``item_link`` for everything in ``items``, without you doing anything.


Writing a renderer
^^^^^^^^^^^^^^^^^^

The most basic renderer would be::

    def myrenderer_yielding():
        yield reverse('app:name')

or::

    def myrenderer():
        return [reverse('app:name')]

Renderers may also be classes::

    class MyRenderer(object):
        __slots__ = ()

        def __init__(self):
            pass

        def __call__(self):
            yield reverse('app:name')


Listening for renders
^^^^^^^^^^^^^^^^^^^^^

There are 7 signals in total:

* ``build_started`` is fired when the management command is run.
* ``reader_started`` is fired when a ``URLReader`` instance begins working.
* ``read_page`` is fired when a ``URLReader`` successfully gets a URL's content.
* ``reader_finished`` is fired when a ``URLReader`` instance completes.
* ``writer_started`` is fired when a ``URLWriter`` instance begins working.
* ``writer_finished`` is fired when the ``URLWriter`` completes
* ``build_finished`` fires at the end of the management command.

Rendering on model change
^^^^^^^^^^^^^^^^^^^^^^^^^

Additionally, there is a listener, ``jackfrost.utils.build_page_for_obj`` which
is suitable for being used as a ``pre_save`` or ``post_save`` receiver for
a ``Model`` instance, and will attempt to build just the ``get_absolute_url`` for
that object.

Defining when a model may build
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a ``Model`` instance implements a ``jackfrost_can_build`` method, this is
checked before building the static page. If ``jackfrost_can_build`` returns
``False``, the page won't get built. Any other value will result in it being
built.

Defining different URLs
^^^^^^^^^^^^^^^^^^^^^^^

If a ``Model`` instance implements a ``jackfrost_absolute_url`` method, this
is used instead of the ``get_absolute_url``.

If the ``Model`` instance has a ``get_list_url`` method, that page will also be
built. Useful for yielding paginated results, etc.

Extras
------

Where possible, ``jackfrost`` will attempt to compensate for redirects (301, 302 etc)
by writing an HTML page with a ``<meta refresh>`` tag pointing at the final
endpoint. The template used is called `301.html`.

Additionally, static pages for 401, 403, 404 and 500 errors will be built
from their respective templates, if they exist. Useful if you want to wire
up Apache ``ErrorDocument`` directives or whatever.


Running the tests (85% coverage)
--------------------------------

Given a complete clone::

    python setup.py test

.. _django-medusa: https://github.com/mtigas/django-medusa
.. _staticfiles: https://docs.djangoproject.com/en/stable/ref/contrib/staticfiles/
.. _Django: https://docs.djangoproject.com/en/stable/
.. _pip: https://pip.pypa.io/en/stable/
.. _django-storages: https://django-storages.readthedocs.org/en/latest/
.. _pytest: http://pytest.org/latest/
.. _django-bakery: http://django-bakery.readthedocs.org/en/latest/
.. _they don't: https://github.com/datadesk/django-bakery/issues/15
.. _sitemaps: https://docs.djangoproject.com/en/stable/ref/contrib/sitemaps/
.. _Django sitemap: https://docs.djangoproject.com/en/stable/ref/contrib/sitemaps/
.. _BaseStaticSiteRenderer: https://github.com/mtigas/django-medusa/blob/master/django_medusa/renderers/base.py
.. _Django RSS Feeds: https://docs.djangoproject.com/en/stable/ref/contrib/syndication/
.. _Feed: https://docs.djangoproject.com/en/stable/ref/contrib/syndication/#feed-class-reference
