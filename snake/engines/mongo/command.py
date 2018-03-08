"""The Mongo Command Collection Module.

This module provides everything required to communicate with the Mongo CommandCollection.
"""

import bson

import gridfs
from motor import motor_asyncio

from snake import enums


class CommandCollection():
    """Synchronous Command Collection.

    Attributes:
        db (obj): The database object
    """
    def __init__(self, db):
        self.db = db

    def clean(self):
        """Clean lost commands from the database.

        This removes any pending or running commands. This is used when snake
        is restarted to clean out commands that will never run.
        """
        documents = self.db.commands.find({'$or': [{'status': enums.Status.PENDING}, {'status': enums.Status.RUNNING}]})
        for document in documents:
            self.db.commands.update_one({'_id': document['_id']}, {'$set': {'status': enums.Status.FAILED}})

    def delete(self, sha256_digest, scale, command):
        """Delete command.

        Args:
            sha256_digest (str): The hash of the file.
            scale (str): The scale.
            command (str): The command.
        """
        return self.db.commands.delete_many({"sha256_digest": sha256_digest, "scale": scale, "command": command})

    def insert(self, document):
        """Insert command.

        Args:
            document (:obj:CommandSchema): The command to insert.

        Returns:
            :obj:`CommandSchema`: The inserted command.
        """
        return self.db.commands.insert_one(document)

    def select(self, sha256_digest, scale, command):
        """Select command.

        Args:
            sha256_digest (str): The hash of the file.
            scale (str): The scale.
            command (str): The command.

        Returns:
            :obj:`CommandSchema`: The selected command.
        """
        return self.db.commands.find_one({"sha256_digest": sha256_digest, "scale": scale, "command": command})

    def select_many(self, sha256_digest=None, scale=None, command=None):
        """Select commands.

        Args:
            sha256_digest (str, optional): The hash of the file. Defaults to None.
            scale (str, optional): The scale. Defaults to None.
            command (str, optional): The command. Defaults to None.

        Returns:
            :obj:`Cursor`: The mongodb cursor.
        """
        data = {"sha256_digest": sha256_digest, "scale": scale, "command": command}
        keys = [k for k, v in data.items() if v is None]
        for k in keys:
            del data[k]
        return self.db.commands.find(data)

    def select_all(self):
        """Select all commands.

        Returns:
            :obj:`Cursor`: The mongodb cursor.
        """
        return self.db.commands.find()

    def update(self, sha256_digest, scale, command, data):
        """Update command.

        Args:
            sha256_digest (str): The hash of the file.
            scale (str): The scale.
            command (str): The command.
            data (:obj:`CommandSchema): The update data.

        Returns:
            :obj:`CommandSchema`: The updated command.
        """
        return self.db.commands.update_one({"sha256_digest": sha256_digest, "scale": scale, "command": command}, {'$set': data})


class AsyncCommandCollection():
    """Asynchronous Command Collection.

    Attributes:
        db (obj): The database object
    """
    def __init__(self, db):
        self.db = db

    def delete(self, sha256_digest, scale, command, callback=None):
        """Delete command.

        Args:
            sha256_digest (str): The hash of the file.
            scale (str): The scale.
            command (str): The command.
            callback (func, optional): The callback function. Defaults to None.
        """
        return self.db.commands.delete_many({"sha256_digest": sha256_digest, "scale": scale, "command": command}, callback=callback)

    def insert(self, document, callback=None):
        """Insert command.

        Args:
            document (:obj:CommandSchema): The command to insert.
            callback (func, optional): The callback function. Defaults to None.

        Returns:
            :obj:`CommandSchema`: The inserted command.
        """
        return self.db.commands.insert_one(document, callback=callback)

    def select(self, sha256_digest, scale=None, command=None, callback=None):
        """Select command.

        Args:
            sha256_digest (str): The hash of the file.
            scale (str): The scale.
            command (str): The command.
            callback (func, optional): The callback function. Defaults to None.

        Returns:
            :obj:`CommandSchema`: The selected command.
        """
        return self.db.commands.find_one({"sha256_digest": sha256_digest, "scale": scale, "command": command}, callback=callback)

    def select_many(self, sha256_digest=None, scale=None, command=None):
        """Select commands.

        Args:
            sha256_digest (str, optional): The hash of the file. Defaults to None.
            scale (str, optional): The scale. Defaults to None.
            command (str, optional): The command. Defaults to None.
            callback (func, optional): The callback function. Defaults to None.

        Returns:
            :obj:`Cursor`: The mongodb cursor.
        """
        data = {"sha256_digest": sha256_digest, "scale": scale, "command": command}
        keys = [k for k, v in data.items() if v is None]
        for k in keys:
            del data[k]
        return self.db.commands.find(data)

    def select_all(self):
        """Select all commands.

        Returns:
            :obj:`Cursor`: The mongodb cursor.
        """
        return self.db.commands.find()

    def update(self, sha256_digest, scale, command, data, callback=None):  # pylint: disable=too-many-arguments
        """Update command.

        Args:
            sha256_digest (str): The hash of the file.
            scale (str): The scale.
            command (str): The command.
            data (:obj:`CommandSchema): The update data.
            callback (func, optional): The callback function. Defaults to None.

        Returns:
            :obj:`CommandSchema`: The updated command.
        """
        return self.db.commands.update_one({"sha256_digest": sha256_digest, "scale": scale, "command": command}, {'$set': data}, callback=callback)

    def replace(self, sha256_digest, scale, command, data, callback=None):  # pylint: disable=too-many-arguments
        """Replace command.

        Args:
            sha256_digest (str): The hash of the file.
            scale (str): The scale.
            command (str): The command.
            data (:obj:`CommandSchema): The replace data.
            callback (func, optional): The callback function. Defaults to None.

        Returns:
            :obj:`CommandSchema`: The replaced command.
        """
        return self.db.commands.replace_one({"sha256_digest": sha256_digest, "scale": scale, "command": command}, data, callback=callback)

# pylint: disable=missing-docstring


class CommandOutputCollection():
    def __init__(self, db):
        self.db = gridfs.GridFSBucket(db)

    def delete(self, file_id):
        if isinstance(file_id, str):
            file_id = bson.ObjectId(file_id)
        self.db.delete(file_id)

    def get(self, file_id):
        if isinstance(file_id, str):
            file_id = bson.ObjectId(file_id)
        grid_out = self.db.open_download_stream(file_id)
        return grid_out.read()

    def put(self, file_name, data):
        return self.db.upload_from_stream(file_name, data)


class AsyncCommandOutputCollection():
    def __init__(self, db):
        self.db = motor_asyncio.AsyncIOMotorGridFSBucket(db)

    async def delete(self, file_id):
        if isinstance(file_id, str):
            file_id = bson.ObjectId(file_id)
        await self.db.delete(file_id)

    async def get(self, file_id):
        if isinstance(file_id, str):
            file_id = bson.ObjectId(file_id)
        grid_out = await self.db.open_download_stream(file_id)
        return await grid_out.read()

    async def put(self, file_name, data):
        return await self.db.upload_from_stream(file_name, data)
