# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.messages.constants import SUCCESS
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from jackfrost.models import ModelRenderer
from jackfrost.models import URLReader
from jackfrost.models import URLWriter


def build_selected(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    app_label = opts.app_label
    try:
        model_name = opts.model_name
    except AttributeError:  # pragma: no cover ... Django 1.5
        model_name = opts.module_name

    # cover per-object permissions too ...
    for obj in queryset:
        if not modeladmin.has_change_permission(request=request, obj=obj):
            raise PermissionDenied("You don't have permission to change %s" % obj.pk)

    class PseudoModelRenderer(ModelRenderer):
            def get_paginated_queryset(self):
                return queryset

    instance_urls = PseudoModelRenderer()()
    if request.POST.get('post'):

        # If ever there were proof I over-engineered the API and should
        # backtrack at some point ... this would be it.
        read = tuple(URLReader(urls=instance_urls)())
        written = tuple(URLWriter(data=read)())

        n = len(written)
        modeladmin.message_user(request, _("Successfully built %(count)d URLs.") % {
                "count": n}, SUCCESS)
        # Return None to display the change list page again.
        return None

    qs_count = len(queryset)
    if qs_count == 1:
        objects_name = force_text(opts.verbose_name)
    else:
        objects_name = force_text(opts.verbose_name_plural)

    try:
        context = modeladmin.admin_site.each_context(request=request)
    except TypeError:  # pragma: no cover ... Django 1.7
        context = modeladmin.admin_site.each_context()
    except AttributeError:  # pragma: no cover ... Django 1.6
        context = {}

    context.update({
        'objects_name': objects_name,
        'buildable_objects': instance_urls,
        'buildable_objects_count': len(instance_urls),
        'title': _("Are you sure?"),
        'queryset': queryset,
        'queryset_count': qs_count,
        'opts': opts,
        'action_checkbox_name': ACTION_CHECKBOX_NAME,
    })

    # Display the confirmation page
    return TemplateResponse(request, modeladmin.delete_selected_confirmation_template or [
        "admin/%s/%s/build_selected_confirmation.html" % (app_label, model_name),
        "admin/%s/build_selected_confirmation.html" % app_label,
        "jackfrost/build_selected_confirmation.html",
    ], context, current_app=modeladmin.admin_site.name)
build_selected.short_description = _("Build static pages for selected %(verbose_name_plural)s")
