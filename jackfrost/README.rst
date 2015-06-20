jackfrost 0.3.0
===============

This package represents the `Django`_ application which should be in your
``INSTALLED_APPS``

Implementation information
--------------------------

The building happens in discrete phases:

* A *renderer* exposes an iterable of URLs (either by returning a
  ``list``/``tuple``/``set`` or by yielding individual values)

  * renderers may be functions or classes, or, I suppose, functions which
    return functions.

* A ``URLCollector`` instance calls a set of *renderers* and reads their
  results into a single collection of URLs.

  * By default, the list of renderers is taken from ``settings.JACKFROST_RENDERERS``

* A ``URLReader`` takes a set of URLs, and reads each URL to get it's content,
  which it keeps in memory to provide to the ``URLWriter``

* A ``URLWriter`` takes a set of URLs and their content, and writes each a storage backend.

  * By default, the backend is a subclass of the standard
    Django `staticfiles`_ one.
  * It can be changed by setting ``JACKFROST_STORAGE`` to the storage backend
    of your choice.
  * It does not need to be the same backend as either ``DEFAULT_FILE_STORAGE``
    or ``STATICFILES_STORAGE``

Package layout
--------------

models
^^^^^^

Provides ``ModelRenderer``, ``URLCollector``, ``URLReader`` and ``URLWriter``.
Also provides compatibility shims ``SitemapRenderer``, ``FeedRenderer``
and ``MedusaRenderer``.

signals
^^^^^^^

Provides ``build_started``, ``build_finished``, ``reader_started``,
``reader_finished``, ``writer_started``,
``writer_finished``, and ``read_page`` which are fired at various, hopefully
obvious, points.

utils
^^^^^

Provides the ``build_page_for_obj`` function, suitable for wiring up to
``pre_save`` or ``post_save`` signals.

.. _Django: https://docs.djangoproject.com/en/stable/
.. _staticfiles: https://docs.djangoproject.com/en/stable/ref/contrib/staticfiles/
