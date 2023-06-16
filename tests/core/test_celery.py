# pylint: disable=missing-docstring

import json

import pytest
from celery.contrib.testing import mocks
from snake import error, schema
from snake.core import celery

# pylint: disable=invalid-name


def test_snake_request_kill_child_processes(mocker):
    """
    Test SnakeRequest: kill_child_processes
    """

    def fake_kill(*args, **kwargs):  # pylint: disable=unused-argument
        raise OSError

    def fake_ps(*args, **kwargs):  # pylint: disable=unused-argument
        class FakePs:  # pylint: disable=too-few-public-methods
            returncode = 0
            stdout = b"1234\n"

        return FakePs()

    mocker.patch("time.sleep")

    SnakeRequest = celery.SnakeRequest

    # Test return failed ps command
    mocker.patch("subprocess.run")
    snake_request = SnakeRequest(mocks.TaskMessage("test"), task="1234")
    snake_request.kill_child_processes(1234)
    mocker.patch("subprocess.run")

    # Test a match and fake kill
    mocker.patch("os.kill")
    mocker.patch("subprocess.run", fake_ps)
    snake_request = SnakeRequest(mocks.TaskMessage("test"), task="1234")
    snake_request.kill_child_processes(1234)
    mocker.patch("os.kill")
    mocker.patch("subprocess.run")

    # Test a no match
    mocker.patch("os.kill")
    mocker.patch("subprocess.run", fake_ps)
    snake_request = SnakeRequest(mocks.TaskMessage("test"), task="1234")
    snake_request.kill_child_processes(4321)
    mocker.patch("os.kill")
    mocker.patch("subprocess.run")

    # Test trying to kill a dead process
    mocker.patch("os.kill", fake_kill)
    mocker.patch("subprocess.run", fake_ps)
    snake_request = SnakeRequest(mocks.TaskMessage("test"), task="1234")
    snake_request.kill_child_processes(1234)
    mocker.patch("os.kill")
    mocker.patch("subprocess.run")


def test_snake_request_on_timeout():
    """
    Test SnakeRequest: timeout
    """

    # pylint: disable=no-member, protected-access

    def kill_child_processes(self, *args, **kwargs):  # pylint: disable=unused-argument
        self.abcd = args

    def _on_timeout(*args, **kwargs):  # pylint: disable=unused-argument
        return

    SnakeRequest = celery.SnakeRequest
    SnakeRequest.kill_child_processes = kill_child_processes
    SnakeRequest._on_timeout = _on_timeout

    # Test soft, is will set optional arg SIGTERM over SIGKILL
    snake_request = SnakeRequest(mocks.TaskMessage("test"), task="1234")
    snake_request.on_timeout(soft=True, timeout=1)
    assert len(snake_request.abcd) == 2

    # Test hard
    snake_request = SnakeRequest(mocks.TaskMessage("test"), task="1234")
    snake_request.on_timeout(soft=False, timeout=1)
    assert len(snake_request.abcd) == 1


def test_execute_command(mocker):
    """
    Test the execute_command function
    """

    # NOTE: The setup probably warrant tests in themselves but this is better than nothing ;)

    base_data = schema.CommandSchema().load(
        {"sha256_digest": "abcd", "scale": "abcd", "command": "abcd"}
    )

    class DataBase:  # pylint: disable=too-few-public-methods
        def __init__(self):  # pylint: disable=unused-argument
            self.data = schema.CommandSchema().dump(base_data)
            self.output = ""

    database = DataBase()

    class CommandCollection:  # pylint: disable=too-few-public-methods, no-self-use
        def __init__(self, db):  # pylint: disable=unused-argument
            self.db = db

        def update(
            self, sha256_digest, scale, command, args, data
        ):  # pylint: disable=unused-argument
            self.db.data = data

    class CommandOutputCollection:  # pylint: disable=too-few-public-methods, no-self-use
        def __init__(self, db):  # pylint: disable=unused-argument
            self.db = db

        def put(self, file_name, data):  # pylint: disable=unused-argument
            self.db.output = data

    class MongoClient:  # pylint: disable=too-few-public-methods
        class Snake:
            def __init__(self, db):  # pylint: disable=unused-argument
                self.snake = db

        def dummy(self, *args, **kwargs):  # pylint: disable=unused-argument
            return self.snake

        __enter__ = dummy
        __exit__ = dummy

        def __init__(self, db):  # pylint: disable=unused-argument
            self.snake = self.Snake(database)

    class ScaleManagerCW:  # pylint: disable=too-few-public-methods
        def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
            raise error.CommandWarning("error")

    class ScaleManagerSE:  # pylint: disable=too-few-public-methods
        def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
            raise error.SnakeError("error")

    class ScaleManagerTE:  # pylint: disable=too-few-public-methods
        def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
            raise BrokenPipeError("error")

    class ScaleManagerE:  # pylint: disable=too-few-public-methods
        def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
            raise Exception("error")

    def dumps(data):
        try:
            return str(data).replace("'", '"')
        except Exception as err:
            return '{"dummy": "%s"}' % err

    mocker.patch("json.dumps", dumps)
    mocker.patch("pymongo.MongoClient", MongoClient)
    mocker.patch("snake.core.scale_manager.ScaleManager")
    mocker.patch("snake.engines.mongo.command.CommandCollection", CommandCollection)
    mocker.patch(
        "snake.engines.mongo.command.CommandOutputCollection", CommandOutputCollection
    )

    # Test success
    data = schema.CommandSchema().dump(base_data)
    celery.execute_command(data)
    assert database.data["status"] == "success"

    # Cause command warning
    mocker.patch("snake.core.scale_manager.ScaleManager", ScaleManagerCW)
    data = schema.CommandSchema().dump(base_data)
    celery.execute_command(data)
    assert database.data["status"] == "failed"
    output = database.output
    if isinstance(output, bytes):
        output = output.decode("utf-8")
    assert "error" in json.loads(output)

    # Cause snake error
    mocker.patch("snake.core.scale_manager.ScaleManager", ScaleManagerSE)
    data = schema.CommandSchema().dump(base_data)
    celery.execute_command(data)
    assert database.data["status"] == "failed"
    output = database.output
    if isinstance(output, bytes):
        output = output.decode("utf-8")
    assert "error" in json.loads(output)

    # Cause timeout error
    mocker.patch("snake.core.scale_manager.ScaleManager", ScaleManagerTE)
    data = schema.CommandSchema().dump(base_data)
    celery.execute_command(data)
    assert database.data["status"] == "failed"
    output = database.output
    if isinstance(output, bytes):
        output = output.decode("utf-8")
    assert "error" in json.loads(output)

    # Cause general error
    mocker.patch("snake.core.scale_manager.ScaleManager", ScaleManagerE)
    data = schema.CommandSchema().dump(base_data)
    celery.execute_command(data)
    assert database.data["status"] == "failed"
    output = database.output
    if isinstance(output, bytes):
        output = output.decode("utf-8")
    assert "error" in json.loads(output)


@pytest.mark.asyncio
async def test_wait_for_task(mocker):
    """
    Test wait_for_task function
    """

    class Task:  # pylint: disable=too-few-public-methods
        result = 1
        set_ready = False

        def ready(self):
            return self.set_ready

    task = Task()

    async def sleep(time):  # pylint: disable=unused-argument
        task.set_ready = True

    mocker.patch("asyncio.sleep", sleep)

    # Test ready task
    task.set_ready = True
    await celery.wait_for_task(task)

    # Test non ready task
    task.set_ready = False
    await celery.wait_for_task(task)
