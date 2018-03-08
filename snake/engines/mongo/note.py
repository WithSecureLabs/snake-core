"""The Mongo Note Collection Module.

This module provides everything required to communicate with the Mongo NoteCollection.
"""


class NoteCollection():
    """Synchronous Note Collection.

    Attributes:
        db (obj): The database object
    """
    def __init__(self, db):
        self.db = db

    def delete(self, sha256_digest):
        """Delete note.

        Args:
            sha256_digest (str): The hash of the file.
        """
        return self.db.notes.delete_many({"sha256_digest": sha256_digest})

    def insert(self, document):
        """Insert note.

        Args:
            document (:obj:CommandSchema): The note to insert.

        Returns:
            :obj:`CommandSchema`: The inserted note.
        """
        return self.db.notes.insert_one(document)

    def select(self, sha256_digest):
        """Select note.

        Args:
            sha256_digest (str): The hash of the file.

        Returns:
            :obj:`CommandSchema`: The selected note.
        """
        return self.db.notes.find_one({"sha256_digest": sha256_digest})

    def select_many(self, sha256_digest):
        """Select notes.

        Args:
            sha256_digest (str): The hash of the file.

        Returns:
            :obj:`Cursor`: The mongodb cursor.
        """
        return self.db.notes.find({"sha256_digest": sha256_digest})

    def select_all(self, filter_=None):
        """Select all notes.

        Args:
            filter_ (dict): The filter. Defaults to None.

        Returns:
            :obj:`Cursor`: The mongodb cursor.
        """
        if filter_:
            return self.db.notes.find(filter_)
        return self.db.notes.find()

    def update(self, sha256_digest, data):
        """Update note.

        Args:
            sha256_digest (str): The hash of the file.
            data (:obj:`CommandSchema): The update data.

        Returns:
            :obj:`CommandSchema`: The updated note.
        """
        return self.db.notes.update_one({"sha256_digest": sha256_digest}, {'$set': data})


class AsyncNoteCollection():
    """Asynchronous Note Collection.

    Attributes:
        db (obj): The database object
    """

    def __init__(self, db):
        self.db = db

    def delete(self, sha256_digest, callback=None):
        """Delete note.

        Args:
            sha256_digest (str): The hash of the file.
            callback (func, optional): The callback function. Defaults to None.
        """
        return self.db.notes.delete_many({"sha256_digest": sha256_digest}, callback=callback)

    def insert(self, document, callback=None):
        """Insert note.

        Args:
            document (:obj:CommandSchema): The note to insert.
            callback (func, optional): The callback function. Defaults to None.

        Returns:
            :obj:`CommandSchema`: The inserted note.
        """
        return self.db.notes.insert_one(document, callback=callback)

    def select(self, sha256_digest, callback=None):
        """Select note.

        Args:
            sha256_digest (str): The hash of the file.
            callback (func, optional): The callback function. Defaults to None.

        Returns:
            :obj:`CommandSchema`: The selected note.
        """
        return self.db.notes.find_one({"sha256_digest": sha256_digest}, callback=callback)

    def select_many(self, sha256_digest):
        """Select notes.

        Args:
            sha256_digest (str): The hash of the file.

        Returns:
            :obj:`Cursor`: The mongodb cursor.
        """
        return self.db.notes.find({"sha256_digest": sha256_digest})

    def select_all(self, filter_=None):
        """Select all notes.

        Args:
            filter_ (dict): The filter. Defaults to None.

        Returns:
            :obj:`Cursor`: The mongodb cursor.
        """
        if filter_:
            return self.db.notes.find(filter_)
        return self.db.notes.find()

    def update(self, sha256_digest, data, callback=None):
        """Update note.

        Args:
            sha256_digest (str): The hash of the file.
            data (:obj:`CommandSchema): The update data.
            callback (func, optional): The callback function. Defaults to None.

        Returns:
            :obj:`CommandSchema`: The updated note.
        """
        return self.db.notes.update_one({"sha256_digest": sha256_digest}, {'$set': data}, callback=callback)
