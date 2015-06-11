from django.dispatch import Signal

build_started = Signal(providing_args=())

build_finished = Signal(providing_args=())

reader_started = Signal(providing_args=('instance',))

reader_finished = Signal(providing_args=('instance',))

read_page = Signal(providing_args=('instance', 'url', 'response', 'filename'))

writer_started = Signal(providing_args=('instance',))

writer_finished = Signal(providing_args=('instance',))
