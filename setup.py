#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
import sys
import os
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


HERE = os.path.abspath(os.path.dirname(__file__))
PYPY = False
CYTHON = False

try:
    # noinspection PyStatementEffect,PyUnresolvedReferences
    sys.pypy_version_info
    PYPY = True
except AttributeError:
    pass

if not PYPY:
    try:
        from Cython.Distutils import build_ext
        CYTHON = True
    except ImportError:
        pass

if CYTHON:
    from setuptools.extension import Extension
    ext_modules = [
        Extension (str('jackfrost.models'),
                   [str(os.path.join('jackfrost', 'models.py'))]),
    ]
    cmdclass = {'build_ext': build_ext}
else:
    ext_modules = []
    cmdclass = {}

class PyTest(TestCommand):
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)
cmdclass.update(test=PyTest)


def make_readme(root_path):
    FILES = ('README.rst', 'LICENSE', 'CHANGELOG', 'CONTRIBUTORS')
    for filename in FILES:
        filepath = os.path.realpath(os.path.join(root_path, filename))
        if os.path.isfile(filepath):
            with open(filepath, mode='r') as f:
                yield f.read()


LONG_DESCRIPTION = "\r\n\r\n----\r\n\r\n".join(make_readme(HERE))


setup(
    name='django-jackfrost',
    version='0.4.0',
    packages=find_packages(),
    install_requires=(
        'Django>=1.5',
    ),
    tests_require=(
        'pytest>=2.6.4',
        'pytest-cov>=1.8.1',
        'pytest-django>=2.8.0',
        'pytest-remove-stale-bytecode>=1.0',
        'pytest-random>=0.2',
        'pytest-sugar>=0.4.0',
        'pytest-spec>=0.2.24',
        'celery>=3.1.18',
        'django-jsonfield>=0.9.13',
        'pinax-eventlog>=1.0.0',
    ),
    cmdclass=cmdclass,
    ext_modules=ext_modules,
    author='Keryn Knight',
    author_email='python-package@kerynknight.com',
    description="A static site generator for Django views",
    long_description=LONG_DESCRIPTION,
    keywords=['django', 'static', 'freeze', 'generator'],
    include_package_data=True,
    url='https://github.com/kezabelle/django-jackfrost',
    download_url='https://github.com/kezabelle/django-jackfrost/releases',
    zip_safe=False,
    license="BSD License",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Environment :: Web Environment',
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Framework :: Django',
        'Framework :: Django :: 1.5',
        'Framework :: Django :: 1.6',
        'Framework :: Django :: 1.7',
        'Framework :: Django :: 1.8',
    ],
)
