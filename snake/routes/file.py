""" The file route module.

Attributes:
    FileHexRoute (tuple): The FileHexRoute.
    FileRoute (tuple): The FileRoute.
    FilesRoute (tuple): The FilesRoute.
"""

from snake import db, enums, error, fields, schema, utils
from snake.core import snake_handler
from tornado import escape
from webargs import tornadoparser

# pylint: disable=abstract-method
# pylint: disable=arguments-differ


class FileHexHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    @snake_handler.authenticated
    async def get(self, sha256_digest):
        document = await db.async_file_collection.select(sha256_digest)
        if not document or document["file_type"] != enums.FileType.FILE:
            self.write_warning(
                "file/hex - no sample for given sha256 digest", 404, sha256_digest
            )
            self.finish()
            return
        file_storage = utils.FileStorage(sha256_digest)
        data = file_storage.to_hexdump(16)
        self.jsonify({"hex": data})
        self.finish()


class FileHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    @snake_handler.authenticated
    async def get(self, sha256_digest):
        document = await db.async_file_collection.select(sha256_digest)
        if not document or document["file_type"] != enums.FileType.FILE:
            self.write_warning(
                "file - no sample for given sha256 digest", 404, sha256_digest
            )
            self.finish()
            return
        document = schema.FileSchema().dump(schema.FileSchema().load(document))
        self.jsonify({"file": document})
        self.finish()

    @snake_handler.authenticated
    async def delete(self, sha256_digest):
        document = await db.async_file_collection.select(sha256_digest)
        if not document or document["file_type"] != enums.FileType.FILE:
            self.write_warning(
                "file - no sample for given sha256 digest", 404, sha256_digest
            )
            self.finish()
            return
        try:
            file_storage = None
            file_storage = utils.FileStorage(sha256_digest)
            file_storage.delete()
        except (
            error.SnakeError
        ):  # Means the file is missing so no harm in removal from db
            pass
        finally:
            if file_storage:
                file_storage.cleanup()
        await db.async_file_collection.delete(sha256_digest)
        self.set_status(200)
        self.jsonify(None)
        self.finish()

    @snake_handler.authenticated
    async def patch(self, sha256_digest):
        # NOTE: We only allow updating of 'description', 'name' and 'tags'
        document = await db.async_file_collection.select(sha256_digest)
        if not document or document["file_type"] != enums.FileType.FILE:
            self.write_warning(
                "file - no sample for given sha256 digest", 404, sha256_digest
            )
            self.finish()
            return
        if not self.request.body:
            self.write_warning("file - no request body found", 422, sha256_digest)
            self.finish()
            return
        data = escape.json_decode(self.request.body)
        data = schema.FileSchema(
            only=("description", "name", "tags"), partial=True
        ).load(data)
        data = schema.FileSchema(only=("description", "name", "tags")).dump(data)
        if data.keys():
            await db.async_file_collection.update(sha256_digest, data)
        document = await db.async_file_collection.select(sha256_digest)
        document = schema.FileSchema().dump(schema.FileSchema().load(document))
        self.jsonify({"file": document})
        self.finish()

    @snake_handler.authenticated
    async def put(self, sha256_digest):
        # NOTE: This is a pseudo PUT as we won't allow clearing of fixed fields
        document = await db.async_file_collection.select(sha256_digest)
        if not document or document["file_type"] != enums.FileType.FILE:
            self.write_warning(
                "file - no sample for given sha256 digest", 404, sha256_digest
            )
            self.finish()
            return
        if not self.request.body:
            self.write_warning("file - no request body found", 422, sha256_digest)
            self.finish()
            return
        data = escape.json_decode(self.request.body)
        if "description" not in data.keys():
            data["description"] = ""
        if "name" not in data.keys():
            data["name"] = ""
        if "tags" not in data.keys():
            data["tags"] = ""
        data = schema.FileSchema(
            only=("description", "name", "tags"), partial=True
        ).load(data)
        data = schema.FileSchema(only=("description", "name", "tags")).dump(data)
        await db.async_file_collection.update(sha256_digest, data)
        document = await db.async_file_collection.select(sha256_digest)
        document = schema.FileSchema().dump(schema.FileSchema().load(document))
        self.jsonify({"file": document})
        self.finish()


class FilesHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    @snake_handler.authenticated
    @tornadoparser.use_args(
        {
            "limit": fields.Str(required=False),
            "operator": fields.Str(required=False, missing="and"),
            "order": fields.Int(required=False, missing=-1),
            "sort": fields.Str(required=False),
        },
        location="querystring",
    )
    async def get(self, data):
        documents = []
        sort = None
        if "sort" in data.keys():
            sort = data["sort"]
        filter_ = self.create_filter(self.request.arguments, data["operator"])
        if filter_:
            filter_ = {"$and": [{"file_type": enums.FileType.FILE}, filter_]}
        else:
            filter_ = {"file_type": enums.FileType.FILE}
        cursor = db.async_file_collection.select_all(filter_, data["order"], sort)
        index = 0
        while await cursor.fetch_next:
            if "limit" in data.keys():
                if index >= int(data["limit"]):
                    break
                index += 1
            documents += [cursor.next_object()]

        documents = schema.FileSchema(many=True).dump(
            schema.FileSchema(many=True).load(documents)
        )
        self.jsonify({"files": documents})
        self.finish()


FileHexRoute = (
    r"/file/(?P<sha256_digest>[a-zA-Z0-9]+)?/hex",
    FileHexHandler,
)  # pylint: disable=invalid-name
FileRoute = (
    r"/file/(?P<sha256_digest>[a-zA-Z0-9]+)?",
    FileHandler,
)  # pylint: disable=invalid-name
FilesRoute = (r"/files", FilesHandler)  # pylint: disable=invalid-name
