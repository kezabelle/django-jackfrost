# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from collections import namedtuple
# noinspection PyUnresolvedReferences
from django.utils.six.moves import input
from itertools import chain
import multiprocessing
from datetime import datetime
from optparse import make_option
import sys
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import BaseCommand
from django.core.management import CommandError
from django.core.management.base import OutputWrapper
from django.test.utils import override_settings
from django.utils.encoding import force_text
# noinspection PyUnresolvedReferences
from django.utils.six.moves import range
from jackfrost.models import URLCollector, URLReader, URLWriter, ErrorReader
from jackfrost.signals import build_started
from jackfrost.signals import build_finished


def multiprocess_reader(urls, stdout=None):
    stdout = OutputWrapper(stdout or sys.stdout)
    result = URLReader(urls=urls)()
    out = set()
    for built_result in result:
        out.add(built_result)
        stdout.write("Read {}".format(built_result.url))
    return out


def multiprocess_writer(data, stdout=None):
    stdout = OutputWrapper(stdout or sys.stdout)
    result = URLWriter(data=data)()
    out = set()
    for built_result in result:
        out.add(built_result)
        if built_result.created:
            stdout.write("Created {}".format(built_result.name))
        elif built_result.modified:
            stdout.write("Updated {}".format(built_result.name))
    return out


class FakeURLConf(namedtuple('FakeURLConf', 'urlpatterns')):
    def __repr__(self):
        return '<%(cls)s [%(count)d]>' % {'mod': self.__module__,
                                          'cls': self.__class__.__name__,
                                          'count': len(self.urlpatterns)}


class Command(BaseCommand):
    help = "Collect Django views into a static folder beneath a static files storage"  # noqa
    requires_system_checks = False

    option_list = BaseCommand.option_list + (
        make_option('--noinput',
            action='store_false', dest='interactive', default=True,
            help="Do NOT prompt the user for input of any kind."),
        make_option('--processes',
            action='store', dest='processes', default=1, type=int,
            help="Number of processes to spawn"),
        make_option('--dry-run',
            action='store_true', dest='dry_run', default=False,
            help="Read all files and run the preview server"),
    )

    @property
    def use_argparse(self):
        return True

    def add_arguments(self, parser):
        parser.add_argument('--noinput',
            action='store_false', dest='interactive', default=True,
            help="Do NOT prompt the user for input of any kind.")
        parser.add_argument('--processes',
            action='store', dest='processes', default=1, type=int,
            help="Number of processes to spawn")
        parser.add_argument('--dry-run',
            action='store_true', dest='dry_run', default=False,
            help="Read all files and run the preview server")

    def set_options(self, **options):
        """
        Set instance variables based on an options dict
        """
        self.interactive = options['interactive']
        self.verbosity = options['verbosity']
        self.processes = options['processes']
        self.multiprocess = options['processes'] > 1
        self.dry_run = options['dry_run']

    def handle_preview(self, read_results):
        if 'django.contrib.staticfiles' in settings.INSTALLED_APPS:
            from django.contrib.staticfiles.management.commands import runserver
        else:
            from django.core.management.commands import runserver

        def filename_len(res):
            return len(res.filename)

        sorted_views = sorted((read_result for read_result in read_results),
                              key=filename_len)
        fake_views = chain.from_iterable(read_result.as_urls()
                                         for read_result in sorted_views)
        urlconf = FakeURLConf(urlpatterns=tuple(fake_views))
        with override_settings(ROOT_URLCONF=urlconf):
            return runserver.Command().handle(use_reloader=False)

    def handle(self, **options):
        self.set_options(**options)
        try:
            collector = URLCollector()
        except ImproperlyConfigured as e:
            raise CommandError(force_text(e))

        collected_urls = collector()
        if not collected_urls:
            raise CommandError("No URLs found after running all defined `JACKFROST_RENDERERS`")


        build_started.send(sender=self.__class__)
        reading_started = datetime.utcnow()

        if self.multiprocess:  # pragma: no cover
            reader_pool = multiprocessing.Pool(processes=self.processes)
            collected_urls = tuple(collected_urls)
            new_urls = tuple(collected_urls[i::self.processes]
                             for i in range(0, self.processes))
            read = reader_pool.map(multiprocess_reader, new_urls)
            reader_pool.close()
            reader_pool.join()
            read_results = tuple(chain.from_iterable(read))
        else:
            read_results = multiprocess_reader(urls=collected_urls,
                                               stdout=self.stdout._out)

        reading_finished = datetime.utcnow()
        reading_duration = reading_finished - reading_started

        self.stdout.write(
            self.style.HTTP_REDIRECT("Read {num} URLs in {time} seconds".format(
                time=reading_duration.total_seconds(), num=len(read_results),
            ))
        )

        if self.dry_run:
            return self.handle_preview(read_results=read_results)

        message = ['\n']
        message.append(
            'You have requested to collect all defined `JACKFROST_RENDERERS` '
            'at the destination\n'
            'location as specified in your settings via `JACKFROST_STORAGE`\n'
        )
        message.append(
            'Are you sure you want to do this?\n\n'
            "Type 'yes' or 'y' to continue: "
        )
        if self.interactive and input(''.join(message)).lower() not in ('yes', 'y'):
            raise CommandError("Collecting cancelled.")

        writing_started = datetime.utcnow()
        if self.multiprocess:  # pragma: no cover
            writer_pool = multiprocessing.Pool(self.processes)
            # noinspection PyUnboundLocalVariable
            written = writer_pool.map(multiprocess_writer, read)
            writer_pool.close()
            writer_pool.join()
            write_results = chain.from_iterable(written)
        else:
            write_results = multiprocess_writer(data=read_results,
                                                stdout=self.stdout._out)

        error_reader = ErrorReader()
        error_results = error_reader()
        written_errors = multiprocess_writer(data=error_results,
                                             stdout=self.stdout._out)

        writing_finished = datetime.utcnow()
        writing_duration = writing_finished - writing_started

        all_written = tuple(chain(write_results, written_errors))

        self.stdout.write(
            self.style.HTTP_REDIRECT("Wrote {num} files in {time} seconds".format(
                time=writing_duration.total_seconds(), num=len(all_written),
            ))
        )
        complete_duration = writing_finished - reading_started
        self.stdout.write(
            self.style.HTTP_REDIRECT("Took {time} seconds total".format(
                time=complete_duration.total_seconds()
            ))
        )
        build_finished.send(sender=self.__class__)
