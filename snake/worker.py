"""The worker module.

This is worker used by celery. They form the snake pit!

Example:
    celery worker --app snake.worker  # Spin a single snake worker

Attributes:
    app (:obj:`Celery`): The celery object used by celery.
"""

from celery import bootsteps
from celery.bin import Option

from snake.config import config_parser
from snake.config import snake_config
from snake.core.celery import celery


class CustomArgs(bootsteps.Step):
    """Custom arguments for celery.

    This allows for a custom configuration file to be passed throught the
    command line. Mainly used for testing.
    """

    def __init__(self, worker, worker_config, **options):  # pylint: disable=super-init-not-called, unused-argument
        if worker_config:
            # NOTE: While the core will have the original settings, as the worker
            # is in effect standalone this should not result in any configuration
            # clashing!
            config_parser.load_config(worker_config[0])
            worker.app.conf.update(**snake_config)


app = celery  # pylint: disable=invalid-name
app.user_options['worker'].add(
    Option('--worker_config', dest='worker_config', default=None, help='Custom worker configuration')
)
app.steps['worker'].add(CustomArgs)
