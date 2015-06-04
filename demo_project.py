#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import os
import sys
from django.conf import settings

DEBUG = os.environ.get('DEBUG', 'on') == 'on'
SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(32))
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

BASE_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
settings.configure(
    DEBUG=DEBUG,
    SECRET_KEY=SECRET_KEY,
    ALLOWED_HOSTS=ALLOWED_HOSTS,
    ROOT_URLCONF='test_urls',  # or __name__ to use local ones ...
    MIDDLEWARE_CLASSES=(
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    },
    TEMPLATE_DIRS=(
        os.path.join(BASE_DIR, 'test_templates'),
    ),
    TEMPLATE_CONTEXT_PROCESSORS=(
        'django.contrib.messages.context_processors.messages',
    ),
    INSTALLED_APPS=(
        'django.contrib.contenttypes',
        'django.contrib.messages',
        'django.contrib.sites',
        'django.contrib.auth',
        'django.contrib.staticfiles',
        'jackfrost',
    ),
    STATIC_ROOT=os.path.join(BASE_DIR, 'test_collectstatic', 'demo_project'),
    STATIC_URL='/__static__/',
    JACKFROST_RENDERERS=('test_urls.UserListRenderer',),
    MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'
)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
