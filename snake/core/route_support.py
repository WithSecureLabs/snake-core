"""The module containing support for router modules.

This contains functions that are shared between the routes modules.
"""

import asyncio
import os
import shutil
import zipfile
from datetime import datetime

from snake import db
from snake import enums
from snake import error
from snake import schema
from snake import utils
from snake.config import snake_config
from snake.core import celery
from snake.managers import scale_manager


async def execute_autoruns(sha256_digest, file_type, mime_type):
    """Find and queue autoruns for a given file (sha256_digest).

    If enabled this function will queue all applicable autoruns for the file
    given (sha256_digest).

    Args:
        sha256_digest (str): The hash of the file to execute the autoruns on.
        file_type (:obj:`FileType`): The file type used to help apply autoruns.
        mime_type (str): The mime type used to help apply autoruns.
    """
    if snake_config['command_autoruns']:
        autoruns = scale_manager.get_autoruns(file_type=file_type)
        for mod, cmd, mime in autoruns:
            if mime and not mime == mime_type:
                continue
            args = {
                'sha256_digest': sha256_digest,
                'scale': mod,
                'command': cmd,
                'asynchronous': True
            }
            args = schema.CommandSchema().load(args)
            await queue_command(args)


async def queue_command(data):
    """Queue commands for execution

    This will queue commands for execution on the celery workers.

    Note:
        The returned command schema will reflect the status of the queued
        command.

    Args:
        data (:obj:`CommandSchema`): The command to queue for execution.

    Returns:
        :obj:`CommandSchema`: The command schema with updates
    """
    # The lastest execution always wins, thus we replace the current one in the db
    document = await db.async_command_collection.select(data['sha256_digest'], data['scale'], data['command'], data['args'])
    if document:
        if 'status' in document and document['status'] == enums.Status.RUNNING:
            return schema.CommandSchema().dump(schema.CommandSchema().load(document))
        else:
            _output_id = None
            if '_output_id' in document:
                _output_id = document['_output_id']
            data['timestamp'] = datetime.utcnow()
            data = schema.CommandSchema().dump(data)
            await db.async_command_collection.replace(data['sha256_digest'], data['scale'], data['command'], data['args'], data)
            # NOTE: We delete after the replace to try and prevent concurrent
            # reads to a file while it is being deleted
            if _output_id:
                await db.async_command_output_collection.delete(_output_id)
    else:
        # Save the command, this will be in a pending state
        data['timestamp'] = datetime.utcnow()
        data = schema.CommandSchema().dump(data)
        await db.async_command_collection.insert(data)

    data = schema.CommandSchema().load(data)
    if data['asynchronous'] is True:
        celery.execute_command.apply_async(args=[data], time_limit=data['timeout'] + 30, soft_time_limit=data['timeout'])
    else:
        task = celery.execute_command.apply_async(args=[data], time_limit=data['timeout'] + 30, soft_time_limit=data['timeout'])
        result = await celery.wait_for_task(task)
        if not task.successful():
            document = await db.async_command_collection.select(data['sha256_digest'], data['scale'], data['command'], data['args'])
            _output_id = None
            if '_output_id' in document:
                _output_id = document['_output_id']
            _new_output_id = await db.async_command_output_collection.put(document['command'], b"{'error': 'worker failed please check log'}")
            document['_output_id'] = _new_output_id
            document['status'] = enums.Status.FAILED
            await db.async_command_collection.update(document['sha256_digest'], document['scale'], document['command'], data['args'], document)
            if _output_id:
                await db.async_command_output_collection.delete(_output_id)
            raise error.SnakeError(result)

    return await db.async_command_collection.select(data['sha256_digest'], data['scale'], data['command'], data['args'])


async def store_file(sha256_digest, file_path, file_type, data):
    """Store a file to disk.

    Uses file storage to store the new file to disk. Upon success insert the
    metadata into the database.

    Args:
        sha256_digest (str): The has of the file to store.
        file_path (str): The location of the file to move into the store.
        file_type (:obj:`FileType`): The type of the file being stored.
        data (:obj:`CommandSchema`): The metadata for the file.

    Returns:
        :obj:`CommandSchema`: The updated document metadata.

    Raises:
        SnakeError: When the metadata cannot be inserted into the database.
    """
    # Save the file to the 'filedb' and add it to the database
    file_storage = utils.FileStorage()
    file_storage.create(file_path, sha256_digest)
    if not file_storage.save(move=True):
        raise error.SnakeError("Failed to store file on disk")
    data.update(file_storage.to_dict())
    data['name'] = strip_extensions(data['name'])
    data['timestamp'] = datetime.utcnow()
    data = schema.FileSchema().dump(data)
    data['file_type'] = file_type  # load_only=True
    document = await db.async_file_collection.insert(data)
    if not document:
        file_storage.delete()
        raise error.SnakeError("Failed to insert document")
    document = await db.async_file_collection.select(file_storage.sha256_digest)

    # Run any autoruns, if allowed
    await execute_autoruns(sha256_digest, file_type, file_storage.mime)

    return document


def strip_extensions(name):
    """Strip extensions from a given name.

    This function is used to strip the trailing extension of a file name. It
    uses a list that is specified in the snake configuration file.

    Note:
        This will only strip the trailing extension, it will not recurse.

    Args:
        name (str): The name to strip.

    Returns:
        str: The stripped name.
    """
    # Strip annoying malware extensions
    if snake_config['strip_extensions']:
        parts = name.rsplit(".", 1)
        if len(parts) > 1:
            for ext in snake_config['strip_extensions']:
                if parts[-1] == ext:
                    return parts[0]
    return name


async def unzip_file_python(file_path, file_name, output_dir, protected=False, password=None):
    """Unzip file using ZipFile.

    Uses ZipFile to extract a file from a zip into a given directory. It will
    handle password protected folders and if no password is presented then it
    will loop through a list of passwords stored in the snake configuration.

    Note:
        Only zips with a single file are supported.

    Args:
        file_path (str): The path to the zipped file.
        file_name (str): The name of the file to extract from the zip.
        output_dir (str): The directory to extract the file to.
        protected (bool, optional): Is the zip password protected. Defaults to False.
        protected (str, optional): The password for the zip. Defaults to None.

    Returns:
        str: The path of the extracted file.

    Raises:
        RuntimeError: For any error that is not related to a Bad Password.
        SnakeError: When extraction of the file has failed.
    """
    zip_file = zipfile.ZipFile(file_path)
    new_path = None
    if protected:
        if password:
            try:
                new_path = zip_file.extract(file_name, output_dir, bytes(password, 'utf-8'))
            except RuntimeError as err:
                if 'Bad password' not in str(err):
                    raise
        else:
            for passwd in snake_config['zip_passwords']:
                try:
                    new_path = zip_file.extract(file_name, output_dir, bytes(passwd, 'utf-8'))
                except RuntimeError as err:
                    if 'Bad password' not in str(err):
                        raise
                if new_path:
                    break
        if not new_path:
            raise error.SnakeError('ZipError: incorrect password')
    else:
        new_path = zip_file.extract(file_name, output_dir, None)
    return new_path


async def unzip_file_unix(file_path, file_name, output_dir, protected=False, password=None):  # pylint: disable=too-many-branches
    """Unzip file using unzip.

    Uses unzip binary to extract a file from a zip into a given directory. It
    will handle password protected folders and if no password is presented then
    it will loop through a list of passwords stored in the snake configuration.

    Note:
        Only zips with a single file are supported.

    Args:
        file_path (str): The path to the zipped file.
        file_name (str): The name of the file to extract from the zip.
        output_dir (str): The directory to extract the file to.
        protected (bool, optional): Is the zip password protected. Defaults to False.
        protected (str, optional): The password for the zip. Defaults to None.

    Returns:
        str: The path of the extracted file.

    Raises:
        SnakeError: When extraction of the file has failed.
    """
    err = ''
    new_path = None
    if protected:
        if password:
            proc = await asyncio.create_subprocess_exec(
                *["unzip", "-P", bytes(password, "utf-8"), "-j", file_path, file_name, "-d", output_dir],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            _stdout, stderr = await proc.communicate()
            if not proc.returncode:
                # NOTE: We flatten dirs so we must strip dirs from file_name if present
                new_path = os.path.join(output_dir, file_name.split('/')[-1])
            else:
                err = str(stderr, encoding='utf-8')
        else:
            for passwd in snake_config['zip_passwords']:
                proc = await asyncio.create_subprocess_exec(
                    *["unzip", "-P", bytes(passwd, "utf-8"), "-j", file_path, file_name, "-d", output_dir],
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE)
                _stdout, stderr = await proc.communicate()
                if not proc.returncode:
                    # NOTE: We flatten dirs so we must strip dirs from file_name if present
                    new_path = os.path.join(output_dir, file_name.split('/')[-1])
                else:
                    err = str(stderr, encoding='utf-8')
                if new_path:
                    break
    else:
        proc = await asyncio.create_subprocess_exec(
            *["unzip", "-j", file_path, file_name, "-d", output_dir],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        _stdout, stderr = await proc.communicate()
        if not proc.returncode:
            # NOTE: We flatten dirs so we must strip dirs from file_name if present
            new_path = os.path.join(output_dir, file_name.split('/')[-1])
        else:
            err = str(stderr, encoding='utf-8')
    if not new_path:
        if 'incorrect password' in err:
            raise error.SnakeError('ZipError: incorrect password')
        else:
            raise error.SnakeError('ZipError: {}'.format(err))

    return new_path


async def unzip_file(file_path, password=None):
    """Unzip a file.

    Unzips a file using unzip or ZipFile. For speed reasons if unzip is
    installed it will be used in favour of the ZipFile library. It will extract
    the file to the same directory as that of the zip folder.

    Note: The zip file must contrail only one file.

    Args:
        file_path (str): The zip file to unzip.
        password (str): The password for the zip. Defaults to None.

    Returns:
        str: The path to the extract file.

    Raises:
        SnakeError: When the zip file contains more than one file.
                    When the extraction fails.
    """
    zip_file = zipfile.ZipFile(file_path)
    info_list = zip_file.infolist()
    if len(info_list) != 1:
        raise error.SnakeError('ZipError: only one file is allowed in the container')
    i = info_list[0]
    working_dir = os.path.dirname(file_path)
    new_path = None
    protected = i.flag_bits & 0x1
    # NOTE: ZipFile is slow as balls so we outsource to unzip if installed
    outsource = shutil.which('unzip')
    if outsource:
        new_path = await unzip_file_unix(file_path, i.filename, working_dir, protected, password)
    else:
        new_path = await unzip_file_python(file_path, i.filename, working_dir, protected, password)
    if not new_path:
        raise error.SnakeError('ZipError: failed to extract file')
    return new_path
