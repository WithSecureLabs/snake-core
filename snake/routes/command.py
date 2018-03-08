""" The command route module.

Attributes:
    CommandRoute (tuple): The CommandRoute.
    CommandsRoute (tuple): The CommandsRoute.
"""

import copy

from marshmallow import exceptions
from webargs import tornadoparser

from snake import db
from snake import enums
from snake import fields
from snake import schema
from snake.core import route_support
from snake.core import snake_handler
from snake.error import ScaleError, SnakeError
from snake.managers import scale_manager


# pylint: disable=abstract-method
# pylint: disable=arguments-differ


def validate_args(cmd, args):
    """Validate arguments.

    Validates the request provided arguments against that expected by the command.

    Args:
        cmd (func): The command function.
        args (dict): The args to validate.
    """
    cmd_args = cmd.cmd_opts.args
    try:
        if cmd_args:
            schema.Schema(fields=copy.deepcopy(cmd_args)).load(args)
    except exceptions.ValidationError as err:
        return False, '{"args": %s}' % err.messages
    return True, None


class CommandHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    @tornadoparser.use_args({
        'command': fields.Str(required=True),
        'format': fields.Str(type=enums.Format, missing=enums.Format.JSON),
        'scale': fields.Str(required=True),
        'sha256_digest': fields.Str(required=True)
    })
    async def get(self, data):
        document = await db.async_command_collection.select(data['sha256_digest'], data['scale'], data['command'])
        if not document:
            self.write_warning("command - no output for given data", 404, data)
            self.finish()
            return

        if document['status'] == enums.Status.ERROR:
            self.write_warning("command - %s" % document['output'], 404, data)
            self.finish()
            return

        document = schema.CommandSchema().load(document)
        output = None
        if document['_output_id']:
            output = await db.async_command_output_collection.get(document['_output_id'])
        try:
            scale = scale_manager.get_scale(data['scale'])
            commands = scale_manager.get_component(scale, enums.ScaleComponent.COMMANDS)
            document['output'] = commands.snake.format(data['format'], document['command'], output)
            document['format'] = data['format']
        except (SnakeError, TypeError) as err:
            self.write_warning("command - %s" % err, 404, data)
            self.finish()
            return

        document = schema.CommandSchema().dump(document)
        self.jsonify({'command': document})
        self.finish()

    @tornadoparser.use_args({
        'args': fields.Dict(required=False, default={}, missing={}),
        'asynchronous': fields.Str(required=False),
        'command': fields.Str(required=True),
        'format': fields.Str(type=enums.Format, missing=enums.Format.JSON),
        'scale': fields.Str(required=True),
        'sha256_digest': fields.Str(required=True),
        'timeout': fields.Int(required=False)
    })
    async def post(self, data):
        # Check that there is a file for this hash
        document = await db.async_file_collection.select(data['sha256_digest'])
        if not document:
            self.write_warning("command - no sample for given data", 404, data)
            self.finish()
            return

        # Check scale support
        try:
            scale = scale_manager.get_scale(data['scale'], document['file_type'])
            commands = scale_manager.get_component(scale, enums.ScaleComponent.COMMANDS)
            cmd = commands.snake.command(data['command'])
        except SnakeError as err:
            self.write_warning("command - %s" % err, 404, data)
            self.finish()
            return

        # Validate arguments as to not waste users time, yes this is also done on execution
        result, args = validate_args(cmd, data['args'])
        if not result:
            self.write_warning("command - %s" % self.json_decode(args.replace("'", '"')), 422)
            self.finish()
            return

        # Queue command
        try:
            document = await route_support.queue_command(data)
        except SnakeError as err:
            self.write_warning("command - %s" % err, 500, data)
            self.finish()
            return

        document = schema.CommandSchema().load(document)
        output = None
        if document['_output_id']:
            output = await db.async_command_output_collection.get(document['_output_id'])
        try:
            document['output'] = commands.snake.format(data['format'], document['command'], output)
            document['format'] = data['format']
        except SnakeError as err:
            self.write_warning("command - %s" % err, 404, data)
            self.finish()
            return

        # Dump and finish
        document = schema.CommandSchema().dump(document)
        self.jsonify({"command": document})
        self.finish()


class CommandsHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    # XXX: Have an 'error' field instead of being silent?
    class GetSchema(schema.Schema):
        """Extends `Schema`.

        Defines the valid schema for get request.
        """
        command = fields.Str(required=False)
        format = fields.Str(type=enums.Format, missing=enums.Format.JSON)
        sha256_digests = fields.List(fields.Str(), required=False)
        scale = fields.Str(required=False)

    class CommandsSchema(schema.Schema):
        """Extends `Schema`.

        Defines the valid schema for post request.
        """
        args = fields.Dict(required=False, default={}, missing={})
        command = fields.Str(required=True)
        format = fields.Str(type=enums.Format, missing=enums.Format.JSON)
        sha256_digests = fields.List(fields.Str(), required=True)
        scale = fields.Str(required=True)
        timeout = fields.Int(required=False)

    async def _get_documents(self, sha, sca, cmd, fmt):
        documents = []
        cur = db.async_command_collection.select_many(sha256_digest=sha, scale=sca, command=cmd)
        while await cur.fetch_next:
            doc = cur.next_object()
            doc = schema.CommandSchema().load(doc)
            try:  # Ignore output for missing scales and/or commands
                scale = scale_manager.get_scale(doc['scale'])
                commands = scale_manager.get_component(scale, enums.ScaleComponent.COMMANDS)
            except Exception as err:
                print("%s - %s" % (doc['scale'], err))  # TODO: Output to log
                continue
            output = None
            if '_output_id' in doc and doc['_output_id']:
                output = await db.async_command_output_collection.get(doc['_output_id'])
            doc = schema.CommandSchema().dump(doc)
            try:
                doc['output'] = commands.snake.format(fmt, cmd, output)
                doc['format'] = fmt
            except (SnakeError, TypeError) as err:
                print("%s - %s" % (doc['scale'], err))  # TODO: Output to log
                continue
            documents += [doc]
        return documents

    @tornadoparser.use_args(GetSchema(many=True))
    async def get(self, data):  # pylint: disable=too-many-branches
        # TODO: Should further clean this
        # We accept RESTful syntax and JSON syntax to allow for increased
        # control. As this is a GET and we are RESTful, URI wins over JSON
        uri_data = {}
        for arg in self.request.arguments:
            if arg == 'sha256_digest':
                uri_data['sha256_digests'] = [self.get_argument(arg)]
            else:
                uri_data[arg] = self.get_argument(arg)
        if uri_data.keys():
            uri_data = self.GetSchema().load(uri_data)
            data = [uri_data]

        documents = []

        # Handle no args, and return early
        if not data:
            try:
                cur = db.async_command_collection.select_all()
                while await cur.fetch_next:
                    documents += [cur.next_object()]
            except SnakeError as err:
                self.write_warning("commands - %s" % err, 404, data)
                self.finish()
                return
            # XXX: Fails to validate -__-
            # documents = schema.CommandSchema(many=True).dump(documents)
            self.jsonify({'commands': documents})
            self.finish()
            return

        # Otherwise build query
        try:
            for i in data:
                scale = i['scale'] if 'scale' in i.keys() else None
                cmd = i['command'] if 'command' in i.keys() else None
                if 'sha256_digests' in i.keys() and i['sha256_digests'] and i['sha256_digests'][0].lower() != 'all':
                    if i['sha256_digests'][0][:4] == 'all:':  # Handle file_type restrictions
                        file_type = enums.FileType(i['sha256_digests'][0].lower().split(':')[1])
                        file_collection = db.async_file_collection.select_many(file_type=file_type)
                        while await file_collection.fetch_next:
                            sha = file_collection.next_object()['sha256_digest']
                            documents += await self._get_documents(sha, scale, cmd, i['format'])
                    else:
                        for sha in i['sha256_digests']:
                            documents += await self._get_documents(sha, scale, cmd, i['format'])
                else:
                    documents += await self._get_documents(None, scale, cmd, i['format'])
        except SnakeError as err:
            self.write_warning("commands - %s" % err, 404, data)
            self.finish()
            return
        self.jsonify({'commands': documents})
        self.finish()

    # pylint: disable=invalid-name
    @tornadoparser.use_args(CommandsSchema(many=True))
    async def post(self, data):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        # XXX: Needs a major clean/rework
        if not data:
            self.write_warning("commands - no request body found", 422, data)
            self.finish()
            return

        # Find the commands and validate their arguments
        for d in data:
            # Find the command
            try:
                s = scale_manager.get_scale(d['scale'])
                c = scale_manager.get_component(s, enums.ScaleComponent.COMMANDS)
                cmd = c.snake.command(d['command'])
            except ScaleError as err:
                self.write_warning(err.message, err.status_code)
                self.finish()
                return

            result, args = validate_args(cmd, d['args'])
            if not result:
                self.write_warning(self.json_decode(args.replace("'", '"')), 422)
                self.finish()
                return

        # Validate hashes and validate them against scales
        missing = []
        unsupported = []
        for d in data:
            s = scale_manager.get_scale(d['scale'])
            for sha in d['sha256_digests']:
                if sha.lower() == 'all':
                    if not s.supports and not len(s.supports) == len([x for x in enums.FileType]):
                        unsupported += [d]
                    break
                elif sha.lower()[:4] == 'all:':
                    file_type = sha.lower().split(':')[1]
                    if file_type == 'file':
                        ft = enums.FileType.FILE
                    elif file_type == 'memory':
                        ft = enums.FileType.MEMORY
                    else:
                        ft = None
                    if ft is None or (s.supports and ft not in s.supports):
                        unsupported += [(sha, s.name)]
                    break
                else:
                    document = await db.async_file_collection.select(sha)
                    if not document:
                        missing += [d]
                    elif s.supports and document['file_type'] not in s.supports:  # Check scale support
                        unsupported += [d]
        if missing:
            self.write_warning("commands - no sample(s) for given data", 404, missing)
            self.finish()
            return
        if unsupported:
            self.write_warning("commands - command unsupported for given data", 422, unsupported)
            self.finish()
            return

        # Queue commands
        documents = []
        for d in data:
            cmd_dict = {}
            for k, v in d.items():
                if k != 'sha256_digests':
                    cmd_dict[k] = v
            cmd_dict['asynchronous'] = True
            for sha in d['sha256_digests']:
                if sha.lower() == 'all':
                    cursor = db.async_file_collection.select_all()
                    while await cursor.fetch_next:
                        cmd_dict['sha256_digest'] = cursor.next_object()['sha256_digest']
                        cmd_d = schema.CommandSchema().load(cmd_dict)
                        documents += [await route_support.queue_command(cmd_d)]
                    break
                elif sha.lower()[:4] == 'all:':
                    ft = sha.lower().split(':')[1]
                    if ft == 'file':
                        ft = enums.FileType.FILE
                    elif ft == 'memory':
                        ft = enums.FileType.MEMORY
                    cursor = db.async_file_collection.select_many(file_type=ft)
                    while await cursor.fetch_next:
                        cmd_dict['sha256_digest'] = cursor.next_object()['sha256_digest']
                        cmd_d = schema.CommandSchema().load(cmd_dict)
                        documents += [await route_support.queue_command(cmd_d)]
                    break
                else:
                    cmd_dict['sha256_digest'] = sha
                    cmd_d = schema.CommandSchema().load(cmd_dict)
                    documents += [await route_support.queue_command(cmd_d)]

        # Dump and finish
        documents = schema.CommandSchema(many=True).load(documents)
        documents = schema.CommandSchema(many=True).dump(documents)
        self.jsonify({"commands": documents})
        self.finish()


CommandRoute = (r"/command", CommandHandler)  # pylint: disable=invalid-name
CommandsRoute = (r"/commands", CommandsHandler)  # pylint: disable=invalid-name
