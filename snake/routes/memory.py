""" The memory route module.

Attributes:
    MemoryRoute (tuple): The MemoryRoute.
    MemoriesRoute (tuple): The MemoriesRoute.
"""

from tornado import escape
from webargs import tornadoparser

from snake import db
from snake import enums
from snake import error
from snake import fields
from snake import schema
from snake import utils
from snake.core import snake_handler


# pylint: disable=abstract-method
# pylint: disable=arguments-differ


class MemoryHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    async def get(self, sha256_digest):
        document = await db.async_file_collection.select(sha256_digest)
        if not document or document['file_type'] != enums.FileType.MEMORY:
            self.write_warning("memory - no sample for given sha256 digest", 404, sha256_digest)
            self.finish()
            return
        document = schema.FileSchema().dump(schema.FileSchema().load(document))
        self.jsonify({'memory': document})
        self.finish()

    async def delete(self, sha256_digest):
        document = await db.async_file_collection.select(sha256_digest)
        if not document or document['file_type'] != enums.FileType.MEMORY:
            self.write_warning("memory - no sample for given sha256 digest", 404, sha256_digest)
            self.finish()
            return
        try:
            file_storage = utils.FileStorage(sha256_digest)
            file_storage.delete()
        except error.SnakeError:
            pass
        await db.async_file_collection.delete(sha256_digest)
        self.set_status(200)
        self.jsonify(None)
        self.finish()

    async def patch(self, sha256_digest):
        document = await db.async_file_collection.select(sha256_digest)
        if not document or document['file_type'] != enums.FileType.MEMORY:
            self.write_warning("memory - no sample for given sha256 digest", 404, sha256_digest)
            self.finish()
            return
        if not self.request.body:
            self.write_warning("memory - no request body found", 422, sha256_digest)
            self.finish()
            return
        data = escape.json_decode(self.request.body)
        data = schema.FileSchema(only=('description', 'name', 'tags'), partial=True).load(data)
        data = schema.FileSchema().dump(data)
        if data.keys():
            await db.async_file_collection.update(sha256_digest, data)
        document = await db.async_file_collection.select(sha256_digest)
        document = schema.FileSchema().dump(schema.FileSchema().load(document))
        self.jsonify({'memory': document})
        self.finish()

    async def put(self, sha256_digest):
        document = await db.async_file_collection.select(sha256_digest)
        if not document or document['file_type'] != enums.FileType.MEMORY:
            self.write_warning("memory - no sample for given sha256 digest", 404, sha256_digest)
            self.finish()
            return
        if not self.request.body:
            self.write_warning("memory - no request body found", 422, sha256_digest)
            self.finish()
            return
        data = escape.json_decode(self.request.body)
        if 'description' not in data.keys():
            data['description'] = ''
        if 'name' not in data.keys():
            data['name'] = ''
        if 'tags' not in data.keys():
            data['tags'] = ''
        data = schema.FileSchema(only=('description', 'name', 'tags'), partial=True).load(data)
        data = schema.FileSchema().dump(data)
        await db.async_file_collection.update(sha256_digest, data)
        document = await db.async_file_collection.select(sha256_digest)
        document = schema.FileSchema().dump(schema.FileSchema().load(document))
        self.jsonify({'memory': document})
        self.finish()


class MemoriesHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    @tornadoparser.use_args({
        'limit': fields.Str(required=False),
        'operator': fields.Str(required=False, missing='and'),
        'order': fields.Int(required=False, missing=-1),
        'sort': fields.Str(required=False),
    })
    async def get(self, data):
        documents = []
        sort = None
        if 'sort' in data.keys():
            sort = data['sort']
        filter_ = self.create_filter(self.request.arguments, data['operator'])
        if filter_:
            filter_ = {
                '$and': [
                    {'file_type': enums.FileType.MEMORY},
                    filter_
                ]
            }
        else:
            filter_ = {'file_type': enums.FileType.MEMORY}
        cursor = db.async_file_collection.select_all(filter_, data['order'], sort)
        index = 0
        while await cursor.fetch_next:
            if 'limit' in data.keys():
                if index >= int(data['limit']):
                    break
                index += 1
            documents += [cursor.next_object()]

        documents = schema.FileSchema(many=True).dump(schema.FileSchema(many=True).load(documents))
        self.jsonify({'memories': documents})
        self.finish()


MemoryRoute = (r"/memory/(?P<sha256_digest>[a-zA-Z0-9]+)?", MemoryHandler)  # pylint: disable=invalid-name
MemoriesRoute = (r"/memories", MemoriesHandler)  # pylint: disable=invalid-name
