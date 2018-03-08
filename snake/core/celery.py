"""All things celery.

This module contains everything needed for snake to communicate with celery.
This means that there are functions that will be shared by snake along with the
snake workers in the snake_pit.

Notes:
    * The code in this file is a bit messy due to some issues that were met
        when using celery. To work around these some assumptions and hacks have
        been used. These have been marked with XXX.

Attributes:
    celery (:obj:`Celery`): The celery object used by snake and celery.

Todo:
    * Address the XXXs found within this file

"""
import asyncio
import logging
import json
import os
import signal
import subprocess
import time
from datetime import datetime

import pymongo
from celery import Celery
from celery import exceptions
from celery.app import task
from celery.worker import request

from snake import enums
from snake import error
from snake import schema
from snake.config import snake_config
from snake.core import scale_manager
from snake.engines.mongo import command


# pylint: disable=abstract-method
# pylint: disable=invalid-name
# pylint: disable=protected-access
# pylint: disable=redefined-outer-name
# pylint: disable=reimported


# XXX: There are some super awful assumptions here to deal with 'stuck' Popen
# processes from causing defunct processes once killed. We add in a sleep to
# hope that the Popen objects will communicate or wait! Killing pgid is not a
# good idea as the worker will die too. A smarter person will be able to fix
# this :)


app_log = logging.getLogger("tornado.application")


class SnakeRequest(request.Request):
    """Extend `Request`.

    This is done to allow us to kill errant child processes as celery does not
    seem to supply this out of the box.
    """

    @staticmethod
    def kill_child_processes(parent_pid, sig=signal.SIGKILL):
        """Kill child processes for the PID supplied

        This will try to look for any children and kill them with the signal
        supplied.

        Args:
            parent_pid (int): The process id for which the children will be
                killed.
            sig (:obj:`int`): The signal used to kill the child processes.
        """
        proc = subprocess.run(
            ['ps', '-o', 'pid', '--ppid', '%d' % parent_pid, '--noheaders'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        if proc.returncode:
            return
        for pid_str in proc.stdout.decode('utf-8').split("\n")[:-1]:
            try:
                os.kill(int(pid_str), sig)
                time.sleep(2)  # Allow subprocess tasks to flush or we will have defunct until the worker exits
            except OSError:
                pass

    def on_timeout(self, soft, timeout):
        """Extend `on_timeout`.

        This overrides `on_timeout` so that when timeout limits are met
        children processes can be killed
        """
        # XXX: The correct way?!
        # super().on_timeout(self, soft, timeout)
        self._on_timeout(soft, timeout)
        if soft:
            self.kill_child_processes(self.worker_pid, signal.SIGTERM)
        else:
            self.kill_child_processes(self.worker_pid)


class SnakeTask(task.Task):
    """Extend `Task`.

    This is a simple extension just used to set the extended Request class.
    """

    Request = SnakeRequest


# XXX: Monkey patch because the recommended method below base=... does not seem
# to be working!
request.Request._on_timeout = request.Request.on_timeout
request.Request.kill_child_processes = SnakeRequest.kill_child_processes
request.Request.on_timeout = SnakeRequest.on_timeout


celery = Celery('snake', **snake_config)

# Hard overrides
celery.conf.update(accept_content=['pickle'])
celery.conf.update(result_serializer='pickle')
celery.conf.update(task_serializer='pickle')


# XXX: The correct way?!
# @celery.task(base=SnakeTask, time_limit=630, soft_time_limit=600)
@celery.task(time_limit=630, soft_time_limit=600)
def execute_command(command_schema):
    """Execute the command on the celery worker

    This is the task used by celery for the workers. It will execute the
    command and update the database as required.

    Args:
        command_schema (:obj:`CommandSchema`): The command schema to execute.
    """
    from snake.config import snake_config  # XXX: Reload config, bit hacky but required
    with pymongo.MongoClient(snake_config['mongodb']) as connection:
        try:
            # NOTE: We assume the _output_id is always NULL!
            command_collection = command.CommandCollection(connection.snake)
            command_output_collection = command.CommandOutputCollection(connection.snake)
            command_schema['start_time'] = datetime.utcnow()
            command_schema['status'] = enums.Status.RUNNING
            command_schema = schema.CommandSchema().dump(command_schema)
            command_collection.update(command_schema['sha256_digest'], command_schema['scale'], command_schema['command'], command_schema)
            command_schema = schema.CommandSchema().load(command_schema)
            scale_manager_ = scale_manager.ScaleManager(command_schema['scale'])
            scale = scale_manager_.get_scale(command_schema['scale'])
            commands = scale_manager_.get_component(scale, enums.ScaleComponent.COMMANDS)
            cmd = commands.snake.command(command_schema['command'])
            output = cmd(args=command_schema['args'], sha256_digest=command_schema['sha256_digest'])
            command_schema['status'] = enums.Status.SUCCESS
        except error.CommandWarning as err:
            output = {'error': str(err)}
            command_schema['status'] = enums.Status.FAILED
            app_log.warning(err)
        except (error.SnakeError, error.MongoError, TypeError) as err:
            output = {'error': str(err)}
            command_schema['status'] = enums.Status.FAILED
            app_log.error(err)
        except (exceptions.SoftTimeLimitExceeded, exceptions.TimeLimitExceeded, BrokenPipeError) as err:
            output = "{'error': 'time limit exceeded'}"
            command_schema['status'] = enums.Status.FAILED
            app_log.exception(err)
        except Exception as err:
            output = "{'error': 'a server side error has occurred'}"
            command_schema['status'] = enums.Status.FAILED
            app_log.exception(err)
        finally:
            command_schema['end_time'] = datetime.utcnow()
            command_schema = schema.CommandSchema().dump(command_schema)
            _output_id = command_output_collection.put(command_schema['command'], bytes(json.dumps(output), 'utf-8'))
            command_schema['_output_id'] = _output_id
            command_collection.update(command_schema['sha256_digest'], command_schema['scale'], command_schema['command'], command_schema)


async def wait_for_task(task):
    """Async wrapper to wait for a synchronous task.

    Does what is says on the tin, is a work around used to allow for
    asynchronous methods to wait on synchronous without blocking.

    Args:
        task: (:obj:`Task`): The celery task to wait on.
    """
    while True:
        if task.ready():
            return task.result
        else:
            await asyncio.sleep(1)
