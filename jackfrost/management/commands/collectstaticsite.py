# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
# noinspection PyUnresolvedReferences
from django.utils.six.moves import input
from itertools import chain
import sys
from django.core.exceptions import ImproperlyConfigured
from django.core.management import BaseCommand
from django.core.management import CommandError
from django.utils.encoding import force_text
from jackfrost.models import URLCollector, URLReader, URLWriter, ErrorReader
from jackfrost.signals import build_started
from jackfrost.signals import build_finished


class Command(BaseCommand):
    help = "Collect Django views into a static folder beneath a static files storage"  # noqa
    requires_system_checks = False

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('--noinput',
            action='store_false', dest='interactive', default=True,
            help="Do NOT prompt the user for input of any kind.")

    def set_options(self, **options):
        """
        Set instance variables based on an options dict
        """
        self.interactive = options['interactive']
        self.verbosity = options['verbosity']

    def handle(self, **options):
        self.set_options(**options)

        try:
            collector = URLCollector()
        except ImproperlyConfigured as e:
            raise CommandError(force_text(e))

        message = ['\n']
        message.append(
            'You have requested to collect all defined `JACKFROST_RENDERERS` '
            'at the destination\n'
            'location as specified in your settings via `JACKFROST_STORAGE`\n'
        )
        message.append(
            'Are you sure you want to do this?\n\n'
            "Type 'yes' to continue, or 'no' to cancel: "
        )
        if self.interactive and input(''.join(message)) != 'yes':
            raise CommandError("Collecting cancelled.")

        collected_urls = collector()
        if not collected_urls:
            raise CommandError("No URLs found after running all defined `JACKFROST_RENDERERS`")
        reader = URLReader(urls=collected_urls)
        reader_results = reader()
        error_reader = ErrorReader()
        error_results = error_reader()
        builder = URLWriter(data=chain(reader_results, error_results))
        build_started.send(sender=builder.__class__)
        for built_result in builder():
            if built_result.created:
                self.stdout.write("Created {}".format(built_result.name))
            elif built_result.modified:
                self.stdout.write("Updated {}".format(built_result.name))
        build_finished.send(sender=builder.__class__)


