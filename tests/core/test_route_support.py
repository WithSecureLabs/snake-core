# pylint: disable=missing-docstring

import pytest

from snake import error
from snake import schema
from snake.config import snake_config
from snake.core import route_support


@pytest.mark.asyncio
async def test_execute_autoruns(mocker):
    """
    Test execute_autoruns function
    """

    state = {
        'queue': []
    }

    def get_autoruns(self, file_type):  # pylint: disable=unused-argument
        return [
            ('1', '1', None),
            ('2', '2', None),
            ('3', '3', None),
            ('4', '4', '4')
        ]

    def get_autoruns_empty(self, file_type):  # pylint: disable=unused-argument
        return []

    async def queue_command(data):  # pylint: disable=unused-argument
        state['queue'] += [data]

    mocker.patch('snake.core.route_support.queue_command', queue_command)

    snake_config['command_autoruns'] = False

    # Test disabled
    await route_support.execute_autoruns('abcd', None, None)
    assert len(state['queue']) == 0  # pylint: disable=len-as-condition

    snake_config['command_autoruns'] = True

    # Test no autoruns
    mocker.patch('snake.core.scale_manager.ScaleManager.get_autoruns', get_autoruns_empty)
    state['queue'] = []
    await route_support.execute_autoruns('abcd', None, None)
    assert len(state['queue']) == 0  # pylint: disable=len-as-condition
    mocker.patch('snake.core.scale_manager.ScaleManager.get_autoruns', get_autoruns_empty)

    # Test autoruns
    mocker.patch('snake.core.scale_manager.ScaleManager.get_autoruns', get_autoruns)
    state['queue'] = []
    await route_support.execute_autoruns('abcd', None, None)
    assert len(state['queue']) == 3
    mocker.patch('snake.core.scale_manager.ScaleManager.get_autoruns', get_autoruns)

    # Test mime
    mocker.patch('snake.core.scale_manager.ScaleManager.get_autoruns', get_autoruns)
    state['queue'] = []
    await route_support.execute_autoruns('abcd', None, '4')
    assert len(state['queue']) == 4
    mocker.patch('snake.core.scale_manager.ScaleManager.get_autoruns', get_autoruns)


@pytest.mark.asyncio
async def test_queue_command(mocker):
    """
    Test queue_command function
    """

    base_data = schema.CommandSchema().load({'sha256_digest': 'abcd', 'scale': 'abcd', 'command': 'abcd'})
    state = {
        'data': {}
    }

    def apply_async(*args, **kwargs):  # pylint: disable=unused-argument
        class Task:  # pylint: disable=too-few-public-methods
            def successful(self):  # pylint: disable=no-self-use
                return True

        state['data'] = kwargs['args'][0]
        state['data']['status'] = 'running'
        return Task()

    def apply_async_fail(*args, **kwargs):  # pylint: disable=unused-argument
        class Task:  # pylint: disable=too-few-public-methods
            def successful(self):  # pylint: disable=no-self-use
                return False

        state['data'] = kwargs['args'][0]
        state['data']['status'] = 'running'
        return Task()

    async def insert(self, *args):  # pylint: disable=unused-argument
        state['data'] = args

    async def put(self, *args):  # pylint: disable=unused-argument
        pass

    async def replace(self, *args):  # pylint: disable=unused-argument
        return state['data']

    async def update_fail(self, *args):  # pylint: disable=unused-argument
        state['data']['status'] = 'failed'

    async def select(self, *args):  # pylint: disable=unused-argument
        return state['data']

    async def wait_for_task(self, *args, **kwargs):  # pylint: disable=unused-argument
        return

    mocker.patch('snake.core.celery.execute_command.apply_async', apply_async)
    mocker.patch('snake.core.celery.wait_for_task', wait_for_task)
    mocker.patch('snake.db.async_command_collection.insert', insert)
    mocker.patch('snake.db.async_command_collection.replace', replace)
    mocker.patch('snake.db.async_command_collection.select', select)

    # Test Status running
    data = base_data
    data['status'] = 'running'
    state['data'] = data
    state['data'] = await route_support.queue_command(data)
    assert state['data']['status'] == 'running'

    # Test replace branch
    data = base_data
    data['status'] = 'success'
    state['data'] = data
    state['data'] = await route_support.queue_command(data)
    assert state['data']['status'] == 'running'

    # Test new command
    state['data'] = {}
    data = base_data
    data['status'] = 'success'
    state['data'] = await route_support.queue_command(data)
    assert state['data']['status'] == 'running'

    # Test async
    state['data'] = {}
    data = base_data
    data['asynchronous'] = 'true'
    data['status'] = 'success'
    state['data'] = await route_support.queue_command(data)
    assert state['data']['status'] == 'running'

    # Test failure
    mocker.patch('snake.core.celery.execute_command.apply_async', apply_async_fail)
    mocker.patch('snake.db.async_command_collection.update', update_fail)
    mocker.patch('snake.db.async_command_output_collection.put', put)
    state['data'] = {}
    data = base_data
    data['asynchronous'] = 'false'
    data['status'] = 'success'
    with pytest.raises(error.SnakeError):
        state['data'] = await route_support.queue_command(data)
    assert state['data']['status'] == 'failed'


@pytest.mark.asyncio
async def test_store_file(mocker):
    """
    Test store_file function
    """

    base_data = schema.FileSchema().load({'name': 'abcd'})
    state = {
        'data': {}
    }

    async def execute_autoruns(self, *args, **kwargs):  # pylint: disable=unused-argument
        pass

    class FileStorage:  # pylint: disable=too-few-public-methods
        def create(*args, **kwargs):  # pylint: disable=unused-argument, no-method-argument, no-self-use
            return False

        def save(*args, **kwargs):  # pylint: disable=unused-argument, no-method-argument, no-self-use
            return False

    class AsyncFileCollection:
        # XXX: Don't add self it breaks the mocks?!
        async def insert(data):  # pylint: disable=unused-argument, no-self-argument
            state['data'] = data
            return state['data']

        async def select(*args, **kwargs):  # pylint: disable=unused-argument, no-method-argument
            return state['data']

    class AsyncFileCollectionFail:
        # XXX: Don't add self it breaks the mocks?!
        async def insert(data):  # pylint: disable=unused-argument, no-self-argument
            return None

        async def select(*args, **kwargs):  # pylint: disable=unused-argument, no-method-argument
            return state['data']

    mocker.patch('snake.core.route_support.db.async_file_collection', AsyncFileCollection)
    mocker.patch('snake.core.route_support.execute_autoruns', execute_autoruns)
    mocker.patch('snake.core.route_support.utils.FileStorage')

    # Test success
    state['data'] = {}
    data = base_data
    document = await route_support.store_file('abcd', 'file', 'abcd', data)
    assert document['name'] == 'abcd'
    assert document['file_type'] == 'abcd'

    # Test failing to create file
    mocker.patch('snake.core.route_support.utils.FileStorage', FileStorage)
    state['data'] = {}
    data = base_data
    with pytest.raises(error.SnakeError):
        await route_support.store_file('abcd', 'file', 'abcd', data)

    # Test failed insert
    mocker.patch('snake.core.route_support.utils.FileStorage')
    mocker.patch('snake.core.route_support.db.async_file_collection', AsyncFileCollectionFail)
    state['data'] = {}
    data = base_data
    with pytest.raises(error.SnakeError):
        await route_support.store_file('abcd', 'file', 'abcd', data)


@pytest.mark.asyncio
async def test_strip_extensions():
    """
    Test strip_extensions function
    """

    # Test no stripping
    snake_config['strip_extensions'] = []
    name = route_support.strip_extensions('abcd.zip')
    assert name == 'abcd.zip'

    snake_config['strip_extensions'] = ['blah', 'zip']

    # Test stripping no extension
    name = route_support.strip_extensions('abcd')
    assert name == 'abcd'

    # Test stripping one extension
    name = route_support.strip_extensions('abcd.zip')
    assert name == 'abcd'

    # Test stripping two extension
    name = route_support.strip_extensions('abcd.blah.zip')
    assert name == 'abcd.blah'


@pytest.mark.asyncio
async def test_unzip_file_python(mocker):
    """
    Test unzip_file_python function
    """

    class ZipFile:  # pylint: disable=too-few-public-methods
        def __init__(self, path):
            pass

        def extract(self, name, directory, password):  # pylint: disable=unused-argument, no-self-use
            if password == b'incorrect':
                raise RuntimeError
            if password == b'bad':
                raise RuntimeError('Bad password')
            return "{}/{}".format(directory, name)

    mocker.patch("snake.core.route_support.zipfile.ZipFile", ZipFile)

    # Test normal unzip
    path = await route_support.unzip_file_python('path', 'name', 'output_dir')
    assert path == 'output_dir/name'

    # Test password unzip
    path = await route_support.unzip_file_python('path', 'name', 'output_dir', True, 'password')
    assert path == 'output_dir/name'

    # Test bad password unzip
    with pytest.raises(error.SnakeError):
        await route_support.unzip_file_python('path', 'name', 'output_dir', True, 'bad')

    # Test unzip error
    with pytest.raises(RuntimeError):
        await route_support.unzip_file_python('path', 'name', 'output_dir', True, 'incorrect')

    # Test auto password unzip
    snake_config['zip_passwords'] = ['bad', 'password']
    path = await route_support.unzip_file_python('path', 'name', 'output_dir', True)
    assert path == 'output_dir/name'

    # Test auto bad password unzip
    snake_config['zip_passwords'] = ['bad']
    with pytest.raises(error.SnakeError):
        await route_support.unzip_file_python('path', 'name', 'output_dir', True)

    # Test auto password unzip error
    snake_config['zip_passwords'] = ['bad', 'incorrect']
    with pytest.raises(RuntimeError):
        await route_support.unzip_file_python('path', 'name', 'output_dir', True)

    # Test auto password unzip no passwords
    snake_config['zip_passwords'] = []
    with pytest.raises(error.SnakeError):
        await route_support.unzip_file_python('path', 'name', 'output_dir', True)


@pytest.mark.asyncio
async def test_unzip_file_unix(mocker):
    """
    Test unzip_file_unix function
    """

    class Proc:  # pylint: disable=too-few-public-methods
        returncode = 0

        def __init__(self, ret=0):
            self.returncode = ret

        async def communicate(self):
            return b'', b''

    async def create_subprocess_exec(*args, **kwargs):  # pylint: disable=unused-argument
        ret = 0
        if args[2] == b'bad':
            ret = 1
        if args[2] == b'incorrect':
            ret = 1
        return Proc(ret)

    mocker.patch("snake.core.route_support.asyncio.create_subprocess_exec", create_subprocess_exec)

    # Test normal unzip
    path = await route_support.unzip_file_unix('path', 'name', 'output_dir')
    assert path == 'output_dir/name'

    # Test password unzip
    path = await route_support.unzip_file_unix('path', 'name', 'output_dir', True, 'password')
    assert path == 'output_dir/name'

    # Test bad password unzip
    with pytest.raises(error.SnakeError):
        await route_support.unzip_file_unix('path', 'name', 'output_dir', True, 'bad')

    # Test unzip error
    with pytest.raises(error.SnakeError):
        await route_support.unzip_file_unix('path', 'name', 'output_dir', True, 'incorrect')

    # Test auto password unzip
    snake_config['zip_passwords'] = ['bad', 'password']
    path = await route_support.unzip_file_unix('path', 'name', 'output_dir', True)
    assert path == 'output_dir/name'

    # Test auto bad password unzip
    snake_config['zip_passwords'] = ['bad']
    with pytest.raises(error.SnakeError):
        await route_support.unzip_file_unix('path', 'name', 'output_dir', True)

    # Test auto password unzip error
    snake_config['zip_passwords'] = ['bad', 'incorrect']
    with pytest.raises(error.SnakeError):
        await route_support.unzip_file_unix('path', 'name', 'output_dir', True)

    # Test auto password unzip no passwords
    snake_config['zip_passwords'] = []
    with pytest.raises(error.SnakeError):
        await route_support.unzip_file_unix('path', 'name', 'output_dir', True)


@pytest.mark.asyncio
async def test_unzip_file(mocker):
    """
    Test unzip_file function
    """

    def no(*args, **kwargs):  # pylint: disable=unused-argument, invalid-name
        return False

    async def dummy(*args, **kwargs):  # pylint: disable=unused-argument
        return 'output_dir/name'

    async def dummy_1(*args, **kwargs):  # pylint: disable=unused-argument
        return None

    class ZipFile:  # pylint: disable=too-few-public-methods
        class Item:
            filename = 'file_name'
            flag_bits = 1

        def __init__(self, path):
            pass

        def infolist(self):  # pylint: disable=no-self-use
            return [self.Item()]

    class ZipFileMulti:  # pylint: disable=too-few-public-methods
        def __init__(self, path):
            pass

        def infolist(self):  # pylint: disable=no-self-use
            return [1, 2]

    mocker.patch("snake.core.route_support.shutil.which")
    mocker.patch("snake.core.route_support.unzip_file_python", dummy)
    mocker.patch("snake.core.route_support.unzip_file_unix", dummy)

    # Test unzip external
    mocker.patch("snake.core.route_support.zipfile.ZipFile", ZipFile)
    path = await route_support.unzip_file('file_path')
    assert path == 'output_dir/name'

    # Test unzip builtin
    mocker.patch("snake.core.route_support.shutil.which", no)
    path = await route_support.unzip_file('file_path')
    assert path == 'output_dir/name'

    # Test unzip failure
    mocker.patch("snake.core.route_support.unzip_file_python", dummy_1)
    with pytest.raises(error.SnakeError):
        await route_support.unzip_file('file_path')

    # Test multiple files
    mocker.patch("snake.core.route_support.zipfile.ZipFile", ZipFileMulti)
    with pytest.raises(error.SnakeError):
        await route_support.unzip_file('file_path')
