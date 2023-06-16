"""The schema module.

This contains the schema used throughout snake.
"""

import copy

import marshmallow

from snake import enums, fields


class Schema(marshmallow.Schema):
    """Extends `Schema`.

    This allows for dynamic creation of a schema which is needed to validate
    arguments within scales.
    """

    class Meta:
        unknown = marshmallow.INCLUDE

    def __init__(self, *args, **kwargs):
        self.additional_fields = kwargs.pop("fields", None)
        super().__init__(*args, **kwargs)
        if self.additional_fields:
            self.declared_fields.update(
                copy.deepcopy(self.additional_fields)
            )  # pylint: disable=no-member
        self._init_fields()


class CommandSchema(Schema):
    """The command schema.

    This is the base schema for the command document stored within the mongo
    database.

    Note:
        Scales are allowed to embed additional information into this document
        but it will be ignored.
    """

    _id = fields.ObjectId(load_only=True)
    _output_id = fields.ObjectId(load_only=True, missing=None)  # GridFS

    sha256_digest = fields.Str(required=True)
    scale = fields.Str(required=True)
    command = fields.Str(required=True)

    args = fields.Dict(default={}, missing={})
    asynchronous = fields.Boolean(default=False)
    timeout = fields.Int(default=600)

    format = fields.Str(type=enums.Format, missing=enums.Format.JSON)
    output = fields.Raw(default=None, missing=None)
    status = fields.Str(
        type=enums.Status, missing=enums.Status.PENDING, default=enums.Status.PENDING
    )

    timestamp = fields.DateTime("%Y-%m-%dT%H:%M:%S.%f")
    start_time = fields.DateTime("%Y-%m-%dT%H:%M:%S.%f")
    end_time = fields.DateTime("%Y-%m-%dT%H:%M:%S.%f")


class FileSchema(Schema):
    """The file schema.

    This is the schema for the file document stored within the mongo database.
    """

    not_blank = marshmallow.validate.Length(min=1, error="Field cannot be blank")

    _id = fields.ObjectId(load_only=True)
    file_type = fields.Enum(type=enums.FileType, load_default=enums.FileType.FILE)

    name = fields.Str(required=True, validate=not_blank)

    sha256_digest = fields.Str()

    description = fields.Str()
    tags = fields.Str()

    magic = fields.Str()
    mime = fields.Str()
    size = fields.Int()

    timestamp = fields.DateTime("%Y-%m-%dT%H:%M:%S.%f")

    submission_type = fields.Str(validate=not_blank, default="unknown")

    parents = fields.Dict(
        values=fields.List(fields.Str(validate=not_blank)),
        keys=fields.Str(validate=not_blank),
        default={},
    )
    children = fields.Dict(
        values=fields.List(fields.Str(validate=not_blank)),
        keys=fields.Str(validate=not_blank),
        default={},
    )


class NoteSchema(Schema):
    """The note schema.

    This is the schema for the note document stored within the mongo database.
    """

    _id = fields.ObjectId(load_only=True)
    sha256_digest = fields.Str(required=True)

    body = fields.Str(required=True)

    timestamp = fields.DateTime("%Y-%m-%dT%H:%M:%S.%f")
    updated_time = fields.DateTime("%Y-%m-%dT%H:%M:%S.%f")
