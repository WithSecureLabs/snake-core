"""The submitter module.

This is used to submit new samples to snake without using the API. This is
useful for scales that wish to upload as part of their workflow.
"""

from datetime import datetime

from snake import db
from snake import error
from snake import schema
from snake.utils import file_storage as fs


def submit(file_schema, file_type, file, parent, scale_name):  # pylint: disable=too-many-branches
    """Submit a new file to Snake.

    This is used generally by the command component of scales to submit a new
    file into snake.

    Args:


    """

    # We need to be safe here so instance check the above
    if not isinstance(file_schema, dict):
        raise TypeError("file_schema must be of type dict")
    if not isinstance(file, fs.FileStorage):
        raise TypeError("file must be of type FileSchema")
    if not isinstance(parent, fs.FileStorage):
        raise TypeError("parent must be of type FileStorage")

    # If the hashes are the same, just stop
    if file.sha256_digest == parent.sha256_digest:
        return db.file_collection.select(file.sha256_digest)

    # Create submission type
    submission_type = 'scale:{}'.format(scale_name)

    # Check if the file to submit is already in Snake, if not lets add it
    document = db.file_collection.select(file.sha256_digest)
    if not document:
        # Validate
        data = schema.FileSchema().dump(schema.FileSchema().load(file_schema))
        # Save the file
        if not file.save(move=True):
            raise error.SnakeError("could not save new file to disk for hash {}".format(file.sha256_digest))
        data.update(file.to_dict())
        # NOTE: Don't set the parent we will do this later, so blank them out
        # if the scale tried to be smart
        data['children'] = {}
        data['parents'] = {}
        data['submission_type'] = submission_type
        data['timestamp'] = datetime.utcnow()
        data = schema.FileSchema().dump(data)
        data['file_type'] = file_type  # load_only=True
        # Save
        db.file_collection.insert(data)

    # Update the parent child relationships
    document = db.file_collection.select(file.sha256_digest)
    if document:
        # Check if the parent and type already exist
        if 'parents' in document and parent.sha256_digest in document['parents']:
            if submission_type in document['parents'][parent.sha256_digest]:
                return document
            else:
                document['parents'][parent.sha256_digest] += [submission_type]
        else:
            document['parents'] = {parent.sha256_digest: [submission_type]}
        # Validate
        document = schema.FileSchema().dump(schema.FileSchema().load(document))
        # Update
        db.file_collection.update(file.sha256_digest, document)

        # Update the parents children
        document = db.file_collection.select(parent.sha256_digest)
        if not document:  # Parent does not exist it has been delete, don't update it
            return db.file_collection.select(file.sha256_digest)
        if 'children' in document and file.sha256_digest in document['children']:
            if submission_type in document['children'][file.sha256_digest]:
                return db.file_collection.select(file.sha256_digest)
            else:
                document['children'][file.sha256_digest] += [submission_type]
        else:
            document['children'] = {file.sha256_digest: [submission_type]}
        # Validate
        document = schema.FileSchema().dump(schema.FileSchema().load(document))
        # Update
        db.file_collection.update(parent.sha256_digest, document)
    else:
        raise error.SnakeError("could not submit new file for hash {}".format(file.sha256_digest))

    return db.file_collection.select(file.sha256_digest)
