""" The store route module.

Attributes:
    StoreRoute (tuple): The StoreRoute.
"""

from snake import db, enums, fields, schema
from snake.core import snake_handler
from webargs import tornadoparser

# pylint: disable=abstract-method
# pylint: disable=arguments-differ


class StoreSampleHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    @snake_handler.authenticated
    async def get(self, sha256_digest):
        document = await db.async_file_collection.select(sha256_digest)
        if not document:
            self.write_warning(
                "store - no sample for given sha256 digest", 404, sha256_digest
            )
            self.finish()
            return
        document = schema.FileSchema().dump(schema.FileSchema().load(document))
        self.jsonify({"sample": document})
        self.finish()


class StoreHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    @snake_handler.authenticated
    @tornadoparser.use_args(
        {
            # filter[field]: str
            "file_type": fields.Enum(type=enums.FileType, required=False, missing=None),
            "from": fields.Int(required=False, missing=0),
            "limit": fields.Int(required=False, missing=10),
            "operator": fields.Str(required=False, missing="and"),
            "order": fields.Int(required=False, missing=-1),
            "sort": fields.Str(required=False, missing=None),
        },
        location="querystring",
    )
    async def get(self, data):
        documents = []
        filter_ = self.create_filter(self.request.arguments, data["operator"])
        if filter_:
            filter_ = {"$and": [filter_]}
            if data["file_type"]:
                filter_["$and"] += [{"file_type": data["file_type"]}]
        elif data["file_type"]:
            filter_ = {"file_type": data["file_type"]}
        # NOTE: With async (motor) there is no count() on cursor so we have to work around that
        total = await db.async_file_collection.db.files.count_documents(
            filter_ if filter_ else {}
        )
        cursor = db.async_file_collection.select_all(
            filter_, data["order"], data["sort"], data["limit"], data["from"]
        )
        while await cursor.fetch_next:
            documents += [cursor.next_object()]

        documents = schema.FileSchema(many=True).dump(
            schema.FileSchema(many=True).load(documents)
        )
        self.jsonify({"samples": documents, "total": total})
        self.finish()


StoreSampleRoute = (
    r"/store/(?P<sha256_digest>[a-zA-Z0-9]+)?",
    StoreSampleHandler,
)  # pylint: disable=invalid-name
StoreRoute = (r"/store", StoreHandler)  # pylint: disable=invalid-name
