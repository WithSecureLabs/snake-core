"""The Mongo File Collection Module.

This module provides everything required to communicate with the Mongo FileCollection.
"""

import pymongo
from pymongo import collation


class FileCollection():
    """Synchronous File Collection.

    Attributes:
        db (obj): The database object
    """

    def __init__(self, db):
        self.db = db

    def delete(self, sha256_digest):
        """Delete file.

        Args:
            sha256_digest (str): The hash of the file.
        """
        return self.db.files.delete_many({"sha256_digest": sha256_digest})

    def insert(self, document):
        """Insert file.

        Args:
            document (:obj:CommandSchema): The file to insert.

        Returns:
            :obj:`CommandSchema`: The inserted file.
        """
        return self.db.files.insert_one(document)

    def select(self, sha256_digest):
        """Select file.

        Args:
            sha256_digest (str): The hash of the file.

        Returns:
            :obj:`CommandSchema`: The selected file.
        """
        return self.db.files.find_one({"sha256_digest": sha256_digest})

    def select_many(self, sha256_digest=None, file_type=None):
        """Select files.

        Args:
            sha256_digest (str, optional): The hash of the file. Defaults to None.
            file_type (:obj:FileType, optional): The file type. Defaults to None.

        Returns:
            :obj:`Cursor`: The mongodb cursor.
        """
        data = {"sha256_digest": sha256_digest, "file_type": file_type}
        keys = [k for k, v in data.items() if v is None]
        for k in keys:
            del data[k]
        return self.db.files.find(data)

    def select_all(self, filter_=None):
        """Select all files.

        Args:
            filter_ (dict): The filter. Defaults to None.

        Returns:
            :obj:`Cursor`: The mongodb cursor.
        """
        if filter_:
            return self.db.files.find(filter_)
        return self.db.files.find()

    def update(self, sha256_digest, data):
        """Update file.

        Args:
            sha256_digest (str): The hash of the file.
            data (:obj:`CommandSchema): The update data.

        Returns:
            :obj:`CommandSchema`: The updated file.
        """
        return self.db.files.update_one({"sha256_digest": sha256_digest}, {'$set': data})


class AsyncFileCollection():
    """Asynchronous File Collection.

    Attributes:
        db (obj): The database object
    """

    def __init__(self, db):
        self.db = db

    def delete(self, sha256_digest, callback=None):
        """Delete file.

        Args:
            sha256_digest (str): The hash of the file.
            callback (func, optional): The callback function. Defaults to None.
        """
        future = self.db.files.delete_many({"sha256_digest": sha256_digest})
        if callback:
            future.add_done_callback(callback)
        return future

    def insert(self, document, callback=None):
        """Insert file.

        Args:
            document (:obj:CommandSchema): The file to insert.
            callback (func, optional): The callback function. Defaults to None.

        Returns:
            :obj:`CommandSchema`: The inserted file.
        """
        future = self.db.files.insert_one(document)
        if callback:
            future.add_done_callback(callback)
        return future

    def select(self, sha256_digest, callback=None):
        """Select file.

        Args:
            sha256_digest (str): The hash of the file.
            callback (func, optional): The callback function. Defaults to None.

        Returns:
            :obj:`CommandSchema`: The selected file.
        """
        future = self.db.files.find_one({"sha256_digest": sha256_digest})
        if callback:
            future.add_done_callback(callback)
        return future

    def select_many(self, sha256_digest=None, file_type=None):
        """Select files.

        Args:
            sha256_digest (str, optional): The hash of the file. Defaults to None.
            file_type (:obj:FileType, optional): The file type. Defaults to None.

        Returns:
            :obj:`Cursor`: The mongodb cursor.
        """
        data = {"sha256_digest": sha256_digest, "file_type": file_type}
        keys = [k for k, v in data.items() if v is None]
        for k in keys:
            del data[k]
        return self.db.files.find(data)

    def select_all(self, filter_=None, order=pymongo.DESCENDING, sort=None):
        """Select all files.

        Args:
            filter_ (dict): The filter. Defaults to None.
            order (:obj:`int`, optional): Sort order. Defaults to DESCENDING.
            sort (dict): Sorting parameters. Defaults to None.

        Returns:
            :obj:`Cursor`: The mongodb cursor.
        """
        documents = []
        if filter_:
            documents = self.db.files.find(filter_)
        else:
            documents = self.db.files.find()
        if sort:
            documents = documents.sort([(sort, order)]).collation(collation.Collation(locale="en"))
        return documents

    def update(self, sha256_digest, data, callback=None):
        """Update file.

        Args:
            sha256_digest (str): The hash of the file.
            data (:obj:`CommandSchema): The update data.
            callback (func, optional): The callback function. Defaults to None.

        Returns:
            :obj:`CommandSchema`: The updated file.
        """
        future = self.db.files.update_one({"sha256_digest": sha256_digest}, {'$set': data})
        if callback:
            future.add_done_callback(callback)
        return future
