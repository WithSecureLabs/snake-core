"""The errors module.

All of the custom exceptions used within snake.
"""


class SnakeError(Exception):
    """The base error class for snake.

    This contains a message, an HTTP status code, and a payload (additional data).

    Attributes:
        message (str): The error message.
        status_code (int): The HTTP status code.
        payload (:obj:): Any additional data.
    """

    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload


# 200
# TODO: Make 200
class CommandWarning(SnakeError):
    """The command warning exception.

    This should be used when a warning needs to be reported from within the
    scale's command component.
    """

    def __init__(self, message):
        SnakeError.__init__(self, message, 500)


class InterfaceWarning(SnakeError):
    """The interface warning exception.

    This should be used when a warning needs to be reported from within the
    scale's interface component.
    """

    def __init__(self, message):
        SnakeError.__init__(self, message, 500)


# 500
class CommandError(SnakeError):
    """The command error exception.

    This should be used when an error needs to be reported from within the
    scale's command component.
    """

    def __init__(self, message):
        SnakeError.__init__(self, message, 500)


class InterfaceError(SnakeError):
    """The interface error exception.

    This should be used when an error needs to be reported from within the
    scale's interface component.
    """

    def __init__(self, message):
        SnakeError.__init__(self, message, 500)


class ScaleError(SnakeError):
    """The scale error exception.

    This should be used when a generic error needs to be reported from within a
    scale.
    """

    def __init__(self, message):
        SnakeError.__init__(self, message, 500)


class UploadError(ScaleError):
    """The upload error exception.

    This should be used when an error needs to be reported from within the
    scale's upload component.
    """

    def __init__(self, message):
        ScaleError.__init__(self, message)


class MongoError(SnakeError):
    """The mongo error exception.

    This should be used when an error needs to be reported that is related to
    mongo.
    """

    def __init__(self, message):
        SnakeError.__init__(self, message, 500)


class ServerError(SnakeError):
    """The server error exception.

    This should be used when an error needs to be reported that is related to
    server side problems, such as missing files.
    """

    def __init__(self, message):
        SnakeError.__init__(self, message, 500)
