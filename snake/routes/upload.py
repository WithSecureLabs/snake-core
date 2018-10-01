""" The file route module.

Attributes:
    UploadFileRoute (tuple): The UploadFileRoute.
    UploadFilesRoute (tuple): The UploadFilesRoute.
    UploadMemoryRoute (tuple): The UploadMemoryRoute.
"""

import hashlib
from os import path

from tornado import escape
from webargs import tornadoparser

from snake import db
from snake import enums
from snake import error
from snake import fields
from snake import schema
from snake.core import route_support
from snake.core import snake_handler


# pylint: disable=arguments-differ


class UploadFileSchema(schema.FileSchema):
    """Extends `FileSchema`."""

    name = fields.Str(required=False)  # Override
    extract = fields.Bool(missing=False)
    password = fields.Str(missing=None)


class UploadFileHandler(snake_handler.StreamHandler):
    """Extends `SnakeHandler`."""

    @tornadoparser.use_args(UploadFileSchema())
    async def post(self, data):
        if data == []:
            self.write_warning("upload/file - no request body found", 422)
            self.finish()
            return

        if 'file' not in self.request.files:
            self.write_warning("upload/file - no 'file' in part", 422)
            self.finish()
            return

        # Set name if missing
        if 'name' not in data:
            data['name'] = self.request.files['file'][0]['filename']

        # Get the files offset and size
        f_path = self.request.files['file'][0]['body'].decode('utf-8')

        # Extract if required, zip only
        if data['extract']:
            try:
                f_path = await route_support.unzip_file(f_path, data['password'])
            except error.SnakeError as err:
                self.write_warning("upload/file - {}".format(err), 422)
                self.finish()
                return
            # Update name if not overriden
            if data['name'] == self.request.files['file'][0]['filename']:
                data['name'] = path.basename(f_path)

        # Set submission type
        data['submission_type'] = 'upload:file'

        # Hash the file
        sha2 = hashlib.sha256()
        with open(f_path, 'rb') as f:
            chunk = f.read(4096)
            while chunk:
                sha2.update(chunk)
                chunk = f.read(4096)
        sha256_digest = sha2.hexdigest()

        # Check if the file already exists
        document = await db.async_file_collection.select(sha256_digest)
        if document:
            document = schema.FileSchema().dump(schema.FileSchema().load(document))
            self.write_warning("upload/file - file already exists for given sha256 digest", 409, {'sample': document})
            self.finish()
            return

        # Save the file and add it to the database
        document = await route_support.store_file(sha256_digest, f_path, enums.FileType.FILE, data)
        document = schema.FileSchema().dump(schema.FileSchema().load(document))
        self.jsonify({'sample': document})
        self.finish()


class UploadFilesHandler(snake_handler.StreamHandler):
    """Extends `SnakeHandler`."""

    async def post(self):
        # XXX: Does not support extraction atm
        #  curl 'http://127.0.0.1:5000/upload/files' -F '0=@./file1' -F '1=@./file2' -F 'data={0:{"name": "file1"}, 1:{"name": "file2"}}'
        #
        data = {}
        try:
            data = self.get_argument('data')
        except Exception:  # noqa
            data = {}
        if data == {}:
            missing_fields = {}
            missing_fields['data'] = ["Missing data for required field."]
            self.write_warning(missing_fields, 422)
            self.finish()
            return
        try:
            data = escape.json_decode(data)
        except Exception:  # noqa
            self.write_warning("upload/files - must be content type application/json", 422, data)
            self.finish()
            return

        # Data is optional we do not check that it keys correctly, to avoid
        # some errors later down the line prevalidate the data dictionaries
        data_arrays = []
        for k, v in data.items():
            if 'name' not in v:
                v['name'] = self.request.files[k][0]['filename']
            data_arrays += [v]

        # Validate with discard we need the keys
        data_arrays = schema.FileSchema(many=True).load(data_arrays)
        schema.FileSchema(many=True).dump(data_arrays)

        # Upload the files
        documents = []
        for k, v in data.items():
            # Set submission type
            v['submission_type'] = 'upload:file'

            # Get the files offset and size
            f_path = self.request.files[k][0]['body'].decode('utf-8')

            # Hash the file
            sha2 = hashlib.sha256()
            with open(f_path, 'rb') as f:
                chunk = f.read(4096)
                while chunk:
                    sha2.update(chunk)
                    chunk = f.read(4096)
            sha256_digest = sha2.hexdigest()

            # Check if the file already exists, if so add to documents, but there is no need to upload it
            document = await db.async_file_collection.select(sha256_digest)
            if document:
                documents += [document]
            else:
                documents += [await route_support.store_file(sha256_digest, f_path, enums.FileType.FILE, v)]
        documents = schema.FileSchema(many=True).dump(schema.FileSchema(many=True).load(documents))
        self.jsonify({'samples': documents})
        self.finish()


class UploadMemoryHandler(snake_handler.StreamHandler):
    """Extends `SnakeHandler`."""

    @tornadoparser.use_args(UploadFileSchema())
    async def post(self, data):
        if data == []:
            self.write_warning("upload/memory - no request body found", 422)
            self.finish()
            return

        if 'file' not in self.request.files:
            self.write_warning("upload/memory - no 'file' in part", 422)
            self.finish()
            return

        # Set name if missing
        if 'name' not in data:
            data['name'] = self.request.files['file'][0]['filename']

        # Get the files offset and size
        f_path = self.request.files['file'][0]['body'].decode('utf-8')

        # Extract if required, zip only
        if data['extract']:
            try:
                f_path = await route_support.unzip_file(f_path, data['password'])
            except error.SnakeError as err:
                self.write_warning("upload/memory - {}".format(err), 422)
                self.finish()
                return
            # Update name if not overriden
            if data['name'] == self.request.files['file'][0]['filename']:
                data['name'] = path.basename(f_path)

        # Set submission type
        data['submission_type'] = 'upload:memory'

        # Hash the file
        sha2 = hashlib.sha256()
        with open(f_path, 'rb') as f:
            chunk = f.read(4096)
            while chunk:
                sha2.update(chunk)
                chunk = f.read(4096)
        sha256_digest = sha2.hexdigest()

        # Check if the file already exists
        document = await db.async_file_collection.select(sha256_digest)
        if document:
            document = schema.FileSchema().dump(schema.FileSchema().load(document))
            self.write_warning("upload/memory - memory already exists for given sha256 digest", 409, {'sample': document})
            self.finish()
            return

        # Save the file and add it to the database
        document = await route_support.store_file(sha256_digest, f_path, enums.FileType.MEMORY, data)
        document = schema.FileSchema().dump(schema.FileSchema().load(document))
        self.jsonify({'sample': document})
        self.finish()


UploadFileRoute = (r"/upload/file", UploadFileHandler)  # pylint: disable=invalid-name
UploadFilesRoute = (r"/upload/files", UploadFilesHandler)  # pylint: disable=invalid-name
UploadMemoryRoute = (r"/upload/memory", UploadMemoryHandler)  # pylint: disable=invalid-name
