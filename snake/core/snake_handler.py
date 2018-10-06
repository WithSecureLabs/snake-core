"""The snake requet handling module.

Basically this is the module that contains all comminality for Tornado based
aspects of snake.

Attributes:
    TAIL_SIZE (int): The size of the sliding window for the stream based
    request handler.
"""

import json
import logging
import tempfile
from datetime import datetime
from os import path

from bson import objectid
from tornado import escape
from tornado import httputil
from tornado import web
from webargs import tornadoparser

from snake import error
from snake.config import constants
from snake.config import snake_config


app_log = logging.getLogger("tornado.application")  # pylint: disable=invalid-name
gen_log = logging.getLogger("tornado.general")  # pylint: disable=invalid-name

TAIL_SIZE = 50


class JSONEncoder(json.JSONEncoder):
    """Extends `JSONEncoder`.

    Define some additional encoding techniques.
    """

    def default(self, o):  # pylint: disable=method-hidden
        """Extends `default`.

        This handles some instances that need a bit of casting in order to encode.
        """
        if isinstance(o, objectid.ObjectId):
            return str(o)
        if isinstance(o, bytes):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


class SnakeHandler(web.RequestHandler):  # pylint: disable=abstract-method
    """Extends `RequestHandler`.

    Defines addtional methods and overrides to suit snake.
    """

    @staticmethod
    def _jsonify(data):
        return JSONEncoder(sort_keys=True, indent=True).encode(data)

    def _write_error_generic(self, status_code):
        self.set_status(status_code)
        self.write({
            "status": "error",
            "message": "snake has encountered an Error!"
        })

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "access-control-allow-origin, x-requested-with, content-type")
        self.set_header('Access-Control-Allow-Methods', 'GET, OPTIONS, PATCH, POST')

    def options(self, *args, **kwargs):
        # NOTE: We only want to push CORS stuff so we don't care about args
        self.set_status(204)
        self.finish()

    def create_filter(self, args, operator):
        """Create a mongo filter.

        Parses a list of request arguments to create a filter for use with mongodb.

        Args:
            args (list): A list of request arguments.
            operator (str): The type of filter.

        Returns:
            dict: The mongodb filter.
        """
        _filter = []
        for arg in args:
            if 'filter' in arg:
                try:
                    f_key = arg.split('[')[1].split(']')[0]
                    for f_arg in self.get_arguments(arg):
                        if '$regex' in f_arg:
                            _filter += [{f_key: escape.json_decode(f_arg)}]
                        else:
                            _filter += [{f_key: f_arg}]
                except Exception:  # noqa
                    pass
        if not _filter:
            return None
        elif len(_filter) == 1:
            _filter = _filter[0]
        else:
            if operator == 'or':
                _filter = {"$or": _filter}
            else:
                _filter = {"$and": _filter}
        return _filter

    def create_args(self, args):
        _args = {}
        for arg in args:
            if 'args' == arg[:4]:
                a_key = arg.split('[')[1].split(']')[0]
                _args[a_key] = self.get_arguments(arg)[0]
        return _args

    @staticmethod
    def json_decode(data):
        """Decode json.

        Decodes json but performs escaping first.

        Args:
            data (str): A json string.

        Returns:
            obj: The decoded json.
        """
        return json.loads(escape.to_basestring(data))

    def jsonify(self, data):
        """Jsonify.

        This creates the response JSON in the format that snake wants and writes it.

        Args:
            data (obj): The data to turn into json.
        """
        resp = {
            "status": "success",
            "data": data
        }
        self.write(JSONEncoder(sort_keys=True, indent=True).encode(resp))

    def write_error(self, status_code, **kwargs):
        """Write an error response.

        This handles the writing and formatting of response errors.

        Args:
            status_code (int): The error code.
            **kwargs: Arbitrary keyword arguments.
        """
        if 'exc_info' not in kwargs:
            self._write_error_generic(status_code)
            return
        _, err, _ = kwargs['exc_info']
        if isinstance(err, tornadoparser.HTTPError):  # Handle webargs/marshmallow fails
            self.write(self._jsonify({
                "status": "fail",
                "message": err.messages
            }))
            return
        if not isinstance(err, error.SnakeError):
            self._write_error_generic(status_code)
            return
        if err.status_code is None:
            self.set_status(status_code)
        else:
            self.set_status(err.status_code)
        self.write(self._jsonify({
            "status": "error",
            "message": err.message
        }))
        return

    def write_warning(self, message, status_code=400, data=None):
        """Write a warning response.

        This handles the writing and formatting of response warnings.

        Args:
            message (str): The warning message
            status_code (int, optional): The status code. Defaults to 400
            data (obj): Additional data for the warning.
        """
        body = {
            "status": "error",
            "message": message
        }
        _message = str(message)
        if data:
            _message += '\n'
            if isinstance(data, dict):
                _message += self._jsonify(data)
            elif isinstance(data, list):
                _message += self._jsonify(data)
            else:
                _message += str(data)

        app_log.warning(_message)

        if data:
            body['data'] = data
        self.set_status(status_code)
        self.write(self._jsonify(body))


class DefaultHandler(SnakeHandler):  # pylint: disable=abstract-method
    """Extend `SnakeHandler`.

    Just the basic default request class for snake that will return a 404 when
    an unknown route is requested.
    """

    async def prepare(self):
        self.write_warning({'api_version': constants.API_VERSION}, 404)
        self.finish()


@web.stream_request_body
class StreamHandler(SnakeHandler):
    """Extend `SnakeHandler`.

    This is the stream handler, it is used to handle large objects without
    eating up all the memory as a traditional Handler would. As a result this
    is quite a complicated class. It will live parse the data as it is being
    recieved and extract any files to disk replacing that data with the paths
    of the extracted files.

    Attributes:
        bytes_read (int): Total number of bytes read.
        content_length (int): Total length of content.
        content_type (str): Type of the content being received.
        data (bytes): The request data but without the file paths instead of the files.
        error (obj): Any error encounterd.
        stream (:obj:`Stream`): The streaming state.
    """

    class Stream():  # pylint: disable=too-few-public-methods
        """The stream state

        This is used to store the state of the streaming data.

        Attributes:
            boundary (str): The request boundary. Used to determine the metadata from the content.
            header (bytes): The header.
            file_count (int): Number of files in the request.
            state (int): The state of the state machine used for live parsing.
            tail (bytes): The tail of the previous chunk.
            working_dir (obj): The `TemporaryDirectory` where the data is being saved to.
        """
        def __init__(self):
            self.boundary = None
            self.header = bytes()
            self.file_count = 0
            self.state = 0
            self.tail = bytes()
            self.working_dir = None

    def initialize(self):
        """Extend `initialize`.

        Works out what sort of request we have and how to parse it. Streaming
        may not actually be required in which case it will not be used.
        """
        self.bytes_read = 0
        self.content_length = 0
        self.content_type = ''
        self.data = bytes()
        self.error = None
        self.stream = None

        if self.request.headers and 'Content-Encoding' in self.request.headers:
            gen_log.warning("Unsupported Content-Encoding: %s", self.request.headers['Content-Encoding'])
            return
        if self.request.headers and 'Content-Type' in self.request.headers:
            self.content_length = int(self.request.headers['Content-Length']) if 'Content-Length' in self.request.headers else 0
            self.content_type = self.request.headers['Content-Type']
            if self.content_type.startswith("application/x-www-form-urlencoded"):
                return
            elif self.content_type.startswith("multipart/form-data"):
                # If we have a POST that is multipart/form-data we will stream any file
                # content to disk. This will prevent excessive RAM usage. Clearly we
                # will need to keep tabs on the overall data size or someone could
                # still use too much RAM!
                self.stream = self.Stream()
                boundary = None
                fields = self.content_type.split(";")
                for field in fields:
                    k, _, v = field.strip().partition("=")
                    if k == "boundary" and v:
                        boundary = bytes(v, 'utf8')
                if not boundary:
                    raise error.SnakeError('Content boundary not found')
                if boundary.startswith(b'"') and boundary.endswith(b'"'):
                    boundary = boundary[1:-1]
                self.stream.boundary = boundary
                self.stream.working_dir = tempfile.TemporaryDirectory(dir=path.abspath(path.expanduser(snake_config['cache_dir'])))
            else:
                self.error = error.SnakeError('Unsupported Content-Type: %s' % self.content_type)

    # NOTE: We are live parsing the request body here using a overlapping
    # sliding window! We need to make sure that this has no errors or we are
    # gonna ingest files incorrectly!!! If anything bad happens we are ducked!
    def data_received(self, chunk):  # pylint: disable=too-many-branches, too-many-statements
        if self.error:
            raise self.error  # pylint: disable=raising-bad-type

        self.bytes_read += len(chunk)

        if len(self.data) > 104857600:  # Ensure the someone is not trying to fill RAM, 100MB
            raise error.SnakeError('Content-Length too large (truncated)')

        if self.stream:  # Cache files to disk
            chunk = self.stream.tail + chunk
            chunk_len = len(chunk)
            i = 0
            while i < chunk_len:
                if self.stream.state == 0:  # Find start of header
                    soh = chunk.find(b'--' + self.stream.boundary, i)
                    if soh != -1:
                        self.data += chunk[soh:soh + len(self.stream.boundary) + 4]
                        i = soh + len(self.stream.boundary) + 4
                        self.stream.state = 1
                        continue
                elif self.stream.state == 1:  # Find end of header
                    eoh = chunk.find(b'\r\n\r\n', i)
                    if eoh != -1:
                        self.stream.header += chunk[i:eoh + 4]
                        i = eoh + 4
                        if b'filename=' in self.stream.header:  # We have a file
                            self.stream.state = 2
                        else:
                            self.stream.state = 3
                        self.data += self.stream.header
                        self.stream.header = bytes()
                        continue
                elif self.stream.state == 2:  # Handle file based content
                    soh = chunk.find(b'--' + self.stream.boundary, i)
                    if soh != -1:
                        f_path = path.join(self.stream.working_dir.name, str(self.stream.file_count))
                        with open(f_path, 'a+b') as f:
                            f.write(chunk[i:soh - 2])  # -2 drops the extra '\r\n'
                        self.data += bytes(f_path + '\r\n', 'utf-8')
                        self.stream.file_count += 1
                        i = soh
                        self.stream.state = 0
                        continue
                elif self.stream.state == 3:  # Handle all other content
                    soh = chunk.find(b'--' + self.stream.boundary, i)
                    if soh != -1:
                        self.data += chunk[i:soh]
                        i = soh
                        self.stream.state = 0
                        continue

                # Handle the overlapping tail
                if i + TAIL_SIZE < chunk_len:
                    if self.stream.state == 2:
                        f_path = path.join(self.stream.working_dir.name, str(self.stream.file_count))
                        with open(f_path, 'a+b') as f:
                            f.write(chunk[i:chunk_len - TAIL_SIZE])
                    elif self.stream.state == 1:
                        self.stream.header += chunk[i:chunk_len - TAIL_SIZE]
                    else:
                        self.data += chunk[i:chunk_len - TAIL_SIZE]
                    self.stream.tail = chunk[chunk_len - TAIL_SIZE:]
                    i += chunk_len
                else:
                    self.stream.tail = chunk[i:]
                    i += chunk_len
        else:  # Otherwise be normal
            self.data += chunk

        if self.bytes_read >= self.content_length:  # Finished, parse the new content
            httputil.parse_body_arguments(self.content_type,
                                          self.data,
                                          self.request.body_arguments,
                                          self.request.files,
                                          headers=None)
            for k, v in self.request.body_arguments.items():
                self.request.arguments.setdefault(k, []).extend(v)

    def on_finish(self):
        if self.stream:
            self.stream.working_dir.cleanup()
