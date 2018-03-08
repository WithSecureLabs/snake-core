"""The database module.

This contains all the databse objects leveraging the engines.

Attributes:
        command_collection (:obj:`CommandCollection`): The synchronous command collection.
        file_collection (:obj:`FileCollection`): The synchronous file collection.
        note_collection (:obj:`NoteCollection`): The synchronous note collection.
        file_output_collection (:obj:`FileOutputCollection`): The synchronous file output collection.
        async_command_collection (:obj:`AsyncCommandCollection`): The asynchronous command collection.
        async_file_collection (:obj:`AsyncFileCollection`): The asynchronous file collection.
        async_note_collection (:obj:`AsyncNoteCollection`): The asynchronous note collection.
        async_file_output_collection (:obj:`AsyncFileOutputCollection`): The asynchronous file output collection.
"""

# pylint: disable=invalid-name
# pylint: disable=unused-import

import pymongo
from motor import motor_asyncio

from snake.config import snake_config
from snake.engines.mongo import command
from snake.engines.mongo import file
from snake.engines.mongo import note


__db__ = pymongo.MongoClient(snake_config['mongodb']).snake
__async_db__ = motor_asyncio.AsyncIOMotorClient(snake_config['mongodb']).snake


command_collection = command.CommandCollection(__db__)
file_collection = file.FileCollection(__db__)
note_collection = note.NoteCollection(__db__)
command_output_collection = command.CommandOutputCollection(__db__)

async_command_collection = command.AsyncCommandCollection(__async_db__)
async_file_collection = file.AsyncFileCollection(__async_db__)
async_note_collection = note.AsyncNoteCollection(__async_db__)
async_command_output_collection = command.AsyncCommandOutputCollection(__async_db__)


def test_connection():
    """Test that the mongodb is reachable.

    Returns:
        bool: True on success, False on failure.
    """
    try:
        pymongo.MongoClient(snake_config['mongodb']).server_info()
    except pymongo.errors.ServerSelectionTimeoutError:
        return False
    return True
