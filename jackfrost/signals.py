from django.dispatch import Signal

build_started = Signal(providing_args=())

build_finished = Signal(providing_args=())

builder_started = Signal(providing_args=('builder'))

builder_finished = Signal(providing_args=('builder'))

built_page = Signal(providing_args=('builder', 'url', 'response', 'filename',
                                    'storage_result'))
