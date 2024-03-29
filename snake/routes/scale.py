""" The file route module.

Attributes:
    ScaleRoute (tuple): The ScaleRoute.
    ScaleCommandsRoute (tuple): The ScaleCommandsRoute.
    ScaleInterfaceRoute (tuple): The ScaleInterfaceRoute.
    ScaleUploadRoute (tuple): The ScaleUploadRoute.
    ScalesRoute (tuple): The ScalesRoute.
"""

import asyncio
import hashlib
import tempfile
from datetime import datetime
from os import path

from marshmallow import exceptions
from snake import db, enums, error, fields, schema
from snake.config import snake_config
from snake.core import route_support, snake_handler
from snake.managers import scale_manager
from tornado import escape
from webargs import tornadoparser

# pylint: disable=abstract-method
# pylint: disable=arguments-differ


class ScaleHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    @snake_handler.authenticated
    async def get(self, scale):
        reload = self.get_argument("reload", "false")
        if reload.lower() == "true":  # Ignore all other values
            scale_manager.reload_scales()
        try:
            _scale = scale_manager.get_scale(scale)
        except error.SnakeError as err:
            self.write_warning("scale - %s" % err, err.status_code, scale)
            self.finish()
            return
        self.jsonify({"scale": _scale.info()})
        self.finish()


class ScaleCommandsHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    @snake_handler.authenticated
    async def get(self, scale):
        try:
            _scale = scale_manager.get_scale(scale)
            commands = scale_manager.get_component(
                _scale, enums.ScaleComponent.COMMANDS
            )
        except error.SnakeError as err:
            self.write_warning("scale - %s" % err, err.status_code, scale)
            self.finish()
            return
        self.jsonify({"commands": commands.snake.info()})
        self.finish()


class ScaleInterfaceHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    class InterfaceSchema(schema.Schema):
        """Extends `Schema`.

        Create schema for interface requests.
        """

        args = fields.Dict(required=False, default={}, missing={})
        command = fields.Str(required=True)
        format = fields.Str(type=enums.Format, missing=enums.Format.JSON)
        sha256_digest = fields.Str(required=True)
        type = fields.Str(type=enums.InterfaceType, missing=enums.InterfaceType.PULL)

    @snake_handler.authenticated
    async def get(self, scale):
        _scale = scale_manager.get_scale(scale)
        interface = scale_manager.get_component(_scale, enums.ScaleComponent.INTERFACE)
        self.jsonify({"interface": interface.snake.info()})
        self.finish()

    @snake_handler.authenticated
    async def post(self, scale):
        if not self.request.body:
            self.write_warning("scale/interface - no request body found", 422, scale)
            self.finish()
            return
        data = escape.json_decode(self.request.body)

        try:
            data = self.InterfaceSchema().dump(self.InterfaceSchema().load(data))
        except exceptions.ValidationError as err:
            self.write_warning(
                self.json_decode(("%s" % err.messages).replace("'", '"')), 422
            )
            self.finish()
            return

        document = await db.async_file_collection.select(data["sha256_digest"])
        if not document:
            self.write_warning("scale/interface - no sample for given data", 404, data)
            self.finish()
            return

        # Get the push/pull and args
        _scale = scale_manager.get_scale(scale)
        interface = scale_manager.get_component(_scale, enums.ScaleComponent.INTERFACE)
        command = scale_manager.get_interface_command(
            interface, data["type"], data["command"]
        )

        data["timestamp"] = datetime.utcnow()

        # Execute command
        # TODO: Handle status don't always chuck errors...
        try:
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(
                None, command, data["args"], data["sha256_digest"]
            )
            # output = p(data['args'], data['sha256_digest'])
        except exceptions.ValidationError as err:
            self.write_warning(
                self.json_decode(('{"args": %s}' % err.messages).replace("'", '"')), 422
            )
            self.finish()
            return
        except error.SnakeError as err:
            self.write_warning("%s" % err, err.status_code, data)
            self.finish()
            return

        # Run formating
        data["output"] = interface.snake.format(data["format"], data["command"], output)

        self.jsonify({"interface": data})
        self.finish()


class ScaleUploadHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    class UploadSchema(schema.FileSchema):
        """Extends `FileSchema`."""

        args = fields.Dict(required=False, default={}, missing={})
        extract = fields.Bool(missing=False)
        name = fields.Str(missing=None)  # Override name
        password = fields.Str(missing=None)

    @snake_handler.authenticated
    async def get(self, scale):
        scale_ = scale_manager.get_scale(scale)
        upload = scale_manager.get_component(scale_, enums.ScaleComponent.UPLOAD)
        self.jsonify({"upload": upload.snake.info()})
        self.finish()

    @snake_handler.authenticated
    async def post(self, scale):  # pylint: disable=too-many-locals
        if not self.request.body:
            self.write_warning("scale/upload - no request body found", 422, scale)
            self.finish()
            return
        data = escape.json_decode(self.request.body)

        # Validate args
        try:
            data = self.UploadSchema().dump(self.UploadSchema().load(data))
        except exceptions.ValidationError as err:
            self.write_warning(
                self.json_decode(("%s" % err.messages).replace("'", '"')), 422
            )
            self.finish()
            return

        scale_ = scale_manager.get_scale(scale)
        upload = scale_manager.get_component(scale_, enums.ScaleComponent.UPLOAD)

        # Validate arguments and update
        upld_args = upload.arguments()
        try:
            if upld_args:
                data["args"] = schema.Schema(fields=upld_args).load(data["args"])
        except exceptions.ValidationError as err:
            self.write_warning(
                self.json_decode(('{"args": %s}' % err.messages).replace("'", '"')), 422
            )
            self.finish()
            return

        # Get the file
        with tempfile.TemporaryDirectory(
            dir=path.abspath(path.expanduser(snake_config["cache_dir"]))
        ) as temp_dir:
            loop = asyncio.get_event_loop()
            f_name = await loop.run_in_executor(
                None, upload.upload, data["args"], temp_dir
            )
            f_path = path.join(temp_dir, f_name)

            # Extract if required, zip only
            if data["extract"]:
                f_path = await route_support.unzip_file(f_path, data["password"])
                f_name = path.basename(f_path)

            # Update name if not overriden
            if not data["name"]:
                data["name"] = f_name

            # Set submission type
            data["submission_type"] = "upload:{}".format(scale)

            # Check that the file is not empty
            if path.getsize(f_path) == 0:
                self.write_warning("scale/upload - sample is empty", 422)
                self.finish()
                return

            # Hash the file
            sha2 = hashlib.sha256()
            with open(f_path, "rb") as f:
                chunk = f.read(4096)
                while chunk:
                    sha2.update(chunk)
                    chunk = f.read(4096)
            sha256_digest = sha2.hexdigest()

            # Check if the file already exists
            document = await db.async_file_collection.select(sha256_digest)
            if document:
                document = schema.FileSchema().dump(schema.FileSchema().load(document))
                self.write_warning(
                    "scale/upload - sample already exists for given sha256 digest",
                    409,
                    {"sample": document},
                )
                self.finish()
                return

            # Save the file and add it to the database
            document = await route_support.store_file(
                sha256_digest, f_path, data["file_type"], data
            )
            document = schema.FileSchema().dump(schema.FileSchema().load(document))
            self.jsonify({"sample": document})
            self.finish()


class ScalesHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    @snake_handler.authenticated
    @tornadoparser.use_args(
        {
            "file_type": fields.Enum(type=enums.FileType, missing=None, required=None),
            "reload": fields.Boolean(missing=False, required=False),
        },
        location="querystring",
    )
    async def get(self, data):
        if data["reload"]:
            scale_manager.reload_scales()
        _scale = scale_manager.get_scales(file_type=data["file_type"])
        self.jsonify({"scales": _scale})
        self.finish()


ScaleRoute = (
    r"/scale/(?P<scale>[^\/]+)?",
    ScaleHandler,
)  # pylint: disable=invalid-name
ScaleCommandsRoute = (
    r"/scale/(?P<scale>[^\/]+)?/commands",
    ScaleCommandsHandler,
)  # pylint: disable=invalid-name
ScaleInterfaceRoute = (
    r"/scale/(?P<scale>[^\/]+)?/interface",
    ScaleInterfaceHandler,
)  # pylint: disable=invalid-name
ScaleUploadRoute = (
    r"/scale/(?P<scale>[^\/]+)?/upload",
    ScaleUploadHandler,
)  # pylint: disable=invalid-name
ScalesRoute = (r"/scales", ScalesHandler)  # pylint: disable=invalid-name
