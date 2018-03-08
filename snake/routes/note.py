""" The note route module.

Attributes:
    NoteRoute (tuple): The NoteRoute.
    NotePostRoute (tuple): The NotePostRoute.
    NotesRoute (tuple): The NotesRoute.
"""

from datetime import datetime

from webargs import tornadoparser

from snake import db
from snake import fields
from snake import schema
from snake.core import snake_handler


# pylint: disable=abstract-method
# pylint: disable=arguments-differ


class NoteHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    async def get(self, sha256_digest):
        document = await db.async_note_collection.select(sha256_digest)
        if not document:
            self.write_warning("note - no sample for given sha256 digest", 404, sha256_digest)
            self.finish()
            return
        document = schema.NoteSchema().dump(schema.NoteSchema().load(document))
        self.jsonify({'note': document})
        self.finish()

    async def delete(self, sha256_digest):
        document = await db.async_note_collection.select(sha256_digest)
        if not document:
            self.write_warning("note - no sample for given sha256 digest", 404, sha256_digest)
            self.finish()
            return
        await db.async_note_collection.delete(sha256_digest)
        self.set_status(200)
        self.jsonify(None)
        self.finish()

    async def patch(self, sha256_digest):
        document = await db.async_note_collection.select(sha256_digest)
        if not document:
            self.write_warning("note - no sample for given sha256 digest", 404, sha256_digest)
            self.finish()
            return
        if not self.request.body:
            self.write_warning("note - no request body found", 422)
            self.finish()
            return
        data = self.json_decode(self.request.body)
        data = schema.NoteSchema(only=('body',)).load(data)
        data['updated_time'] = datetime.utcnow()
        data = schema.NoteSchema().dump(data)
        if data.keys():
            await db.async_note_collection.update(sha256_digest, data)
        document = await db.async_note_collection.select(sha256_digest)
        document = schema.NoteSchema().dump(schema.NoteSchema().load(document))
        self.jsonify({'note': document})
        self.finish()

    async def put(self, sha256_digest):
        document = await db.async_note_collection.select(sha256_digest)
        if not document:
            self.write_warning("note - no sample for given sha256 digest", 404, sha256_digest)
            self.finish()
            return
        if not self.request.body:
            self.write_warning("note - no request body found", 422)
            self.finish()
            return
        data = self.json_decode(self.request.body)
        if 'body' not in data.keys():
            data['body'] = ''
        data = schema.NoteSchema(only=('body',)).load(data)
        data['updated_time'] = datetime.utcnow()
        data = schema.NoteSchema().dump(data)
        await db.async_note_collection.update(sha256_digest, data)
        document = await db.async_note_collection.select(sha256_digest)
        document = schema.NoteSchema().dump(schema.NoteSchema().load(document))
        self.jsonify({'note': document})
        self.finish()


class NotePostHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    @tornadoparser.use_args(schema.NoteSchema())
    async def post(self, data):
        document = await db.async_file_collection.select(data['sha256_digest'])
        if not document:
            self.write_warning("note - no sample for given data", 404, data)
            self.finish()
            return
        document = await db.async_note_collection.select(data['sha256_digest'])
        if document:
            document = schema.NoteSchema().dump(schema.NoteSchema().load(document))
            self.write_warning("note - note already exists for given data", 409, {'note': document})
            self.finish()
            return
        data['timestamp'] = datetime.utcnow()
        data = schema.NoteSchema().dump(data)
        await db.async_note_collection.insert(data)
        document = await db.async_note_collection.select(data['sha256_digest'])
        document = schema.NoteSchema().dump(schema.NoteSchema().load(document))
        self.jsonify({'note': document})
        self.finish()


class NotesHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    @tornadoparser.use_args({
        'sha256_digest': fields.Str(required=False),
    })
    async def get(self, data):
        documents = []
        if 'sha256_digest' in data.keys():
            cursor = db.async_note_collection.select_many(data['sha256_digest'])
            while await cursor.fetch_next:
                documents += [cursor.next_object()]
        else:
            cursor = db.async_note_collection.select_all()
            while await cursor.fetch_next:
                documents += [cursor.next_object()]
        documents = schema.NoteSchema(many=True).dump(schema.NoteSchema(many=True).load(documents))
        self.jsonify({'notes': documents})
        self.finish()

    @tornadoparser.use_args(schema.NoteSchema(many=True))
    async def post(self, data):
        if data == []:
            self.write_warning("note - no request body found", 422)
            self.finish()
            return

        # Check that there is a file for each hash
        missing = []
        for i in data:
            document = await db.async_file_collection.select(i['sha256_digest'])
            if not document:
                missing += [i]
        if missing:
            self.write_warning("note - no sample for given data", 404, missing)
            self.finish()
            return

        # Check that there is a note for each hash
        exists = []
        for i in data:
            document = await db.async_note_collection.select(i['sha256_digest'])
            if document:
                exists += [schema.NoteSchema().dump(schema.NoteSchema().load(document))]
        if exists:
            self.write_warning("note - note already exists for given data", 409, exists)
            self.finish()
            return

        documents = []
        timestamp = datetime.utcnow()
        for i in data:
            i['timestamp'] = timestamp
            i = schema.NoteSchema().dump(i)
            await db.async_note_collection.insert(i)
            documents += [await db.async_note_collection.select(i['sha256_digest'])]
        documents = schema.NoteSchema(many=True).dump(schema.NoteSchema(many=True).load(documents))
        self.jsonify({'notes': documents})
        self.finish()


NoteRoute = (r"/note/(?P<sha256_digest>[a-zA-Z0-9]+)?", NoteHandler)  # pylint: disable=invalid-name
NotePostRoute = (r"/note", NotePostHandler)  # pylint: disable=invalid-name
NotesRoute = (r"/notes", NotesHandler)  # pylint: disable=invalid-name
