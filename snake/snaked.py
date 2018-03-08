#!/usr/bin/python3
"""The snake daemon.

This is snake. This is how snake is loaded, usually this file is called through
a service but it can also be called from the command line (usually for
debug/development purposes).

Examples:
    snaked  # Run snake (if installed with pip).
    python -m snake.snaked -d  # Run snake and output log to console.

Attributes:
    BANNER (str): The snake banner, used in the logs and console.
"""

import argparse
import logging
import os
from os import path
import shutil
import sys
import time

from celery.task.control import inspect  # pylint: disable=import-error, no-name-in-module
from tornado.options import options
from tornado import ioloop, web
from tornado.log import enable_pretty_logging

from snake.config import constants
from snake.config import config_parser
from snake.config import snake_config


# pylint: disable=too-many-locals


BANNER = """
     _   _   _   _     _   _   _   _     _   _   _   _     _           _     _   _   _   _
    |_| |_| |_| |_|   |_| |_| |_| |_|   |_| |_| |_| |_|   |_|         |_|   |_| |_| |_| |_|
     _                 _           _     _           _     _           _     _
    |_|               |_|         |_|   |_|         |_|   |_|         |_|   |_|
     _                 _           _     _           _     _       _         _
    |_|               |_|         |_|   |_|         |_|   |_|     |_|       |_|
     _   _   _   _     _           _     _   _   _   _     _   _             _   _   _   _
    |_| |_| |_| |_|   |_|         |_|   |_| |_| |_| |_|   |_| |_|           |_| |_| |_| |_|
                 _     _           _     _           _     _       _         _
                |_|   |_|         |_|   |_|         |_|   |_|     |_|       |_|
                 _     _           _     _           _     _           _     _
                |_|   |_|         |_|   |_|         |_|   |_|         |_|   |_|
     _   _   _   _     _           _     _           _     _           _     _   _   _   _
    |_| |_| |_| |_|   |_|         |_|   |_|         |_|   |_|         |_|   |_| |_| |_| |_|

    By Countercept, Version {}

""".format(constants.VERSION)


def main(config_file=None, debug=False, pidfile=None):  # pylint: disable=too-many-branches, too-many-statements
    """The main function for snake.

    Runs snake, what more do you need?

    Args:
        config_file (str, optional): Path to a custom configuration file.
            Defaults to None.
        debug (bool): Whether to debug or not. Defaults to False.
            This will direct log output to console.
        pidfile (str, optional): Path to pidfile. Defaults to None.
            This is used by the systemd snake service.
    """

    # Allow PID file creation for use by systemd
    if pidfile:
        if path.isfile(pidfile):
            print('Snake server is already running')
            sys.exit(1)
        with open(pidfile, 'w') as pid:
            pid.write(str(os.getpid()))

    # If user specified reload config file
    if config_file:
        config_parser.load_config(config_file)

    # Check all dirs exist otherwise give up
    keys = ['cache_dir', 'file_db', 'log_dir']
    for key in keys:
        directory = path.abspath(path.expanduser(config_parser.snake_config[key]))
        if not path.exists(directory):
            print("Directory for '{}' does not exist: {}".format(key, directory))
            exit(1)

    # Log to console or file
    if not debug:
        log_dir = path.abspath(path.expanduser(config_parser.snake_config['log_dir']))
        options.log_file_prefix = path.join(log_dir, 'snake.log')
        with open(path.join(log_dir, 'snake.log'), 'w+') as f:
            f.write(BANNER)
    else:
        print(BANNER)

    # Bring in all the snake imports after config is setup
    from snake.core.celery import celery
    from snake.core.route_manager import generate_routes
    from snake.core.snake_handler import DefaultHandler
    from snake import db

    # Logging
    enable_pretty_logging()
    app_log = logging.getLogger("tornado.application")

    # Test mongo connection
    if not db.test_connection():
        app_log.error('failed to connect to mongo server')
        sys.exit(1)

    # Test celery
    try:
        insp = inspect(app=celery, timeout=1.0)
        count = 0
        fail = True
        while count < 4:
            if insp.stats():
                fail = False
                break
            time.sleep(5)
            count += 1
        if fail:
            app_log.error('failed to find any running Celery workers')
            exit(1)
    except IOError as err:
        app_log.error('failed to connect to backend - %s', err)
        sys.exit(1)

    # Run DB command cleaning
    db.command_collection.clean()

    # Clear the cache
    cache_dir = path.abspath(path.expanduser(snake_config['cache_dir']))
    if path.exists(cache_dir):
        for i in os.listdir(cache_dir):
            f = path.join(cache_dir, i)
            if path.isfile(f):
                os.unlink(f)
            else:
                shutil.rmtree(f)

    # Routes
    routes = generate_routes()

    # Spin up
    ioloop.IOLoop.configure('tornado.platform.asyncio.AsyncIOMainLoop')
    application = web.Application(
        routes,
        debug=debug,
        autoreload=debug,
        default_handler_class=DefaultHandler
    )
    application.listen(snake_config['port'], address=snake_config['address'], max_buffer_size=10485760000)  # Set a 10GB limit
    ioloop.IOLoop.current().start()


def __main__():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_file", dest="config_file", default=None, help="custom config path")
    parser.add_argument("-d", "--debug", action='store_true', dest="debug", default=False, help="enable debug mode")
    parser.add_argument("--pidfile", dest="pidfile", default=None, help="path to PID file")
    args = parser.parse_args()
    main(config_file=args.config_file, debug=args.debug, pidfile=args.pidfile)


if __name__ == "__main__":
    __main__()
