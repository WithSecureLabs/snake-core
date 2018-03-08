"""The enums module.

This contains all the enums used in snake.
"""


# pylint: disable=too-few-public-methods


class IterableType(type):
    """Base enum class.

    This allows for iteration through the class variables. A little crude but
    works for what is required.
    """

    def __iter__(cls):
        for attr in dir(cls):
            if not attr.startswith("__"):
                yield cls.__getattribute__(cls, attr)


class FileType(metaclass=IterableType):
    """FileType enum.

    This is used to handle the type of files stored within the file database.
    Currently this can be between: FILE & MEMORY.
    """

    FILE = 'file'
    MEMORY = 'memory'

    def __new__(cls, value):
        if value in FileType:
            return value
        raise ValueError('%s is not a valid FileType' % value)


class Format(metaclass=IterableType):
    """Format enum.

    This is used to handle the supported output types for response data.
    """

    JSON = 'json'
    MARKDOWN = 'markdown'
    PLAINTEXT = 'plaintext'

    def __new__(cls, value):
        if value in Format:
            return value
        raise ValueError('%s is not a valid Format' % value)


class InterfaceType(metaclass=IterableType):
    """Interface command type enum.

    This is used to handle the command types for interfaces.
    """

    PULL = 'pull'
    PUSH = 'push'

    def __new__(cls, value):
        if value in InterfaceType:
            return value
        raise ValueError('%s is not a valid InterfaceType' % value)


class ScaleComponent(metaclass=IterableType):
    """Scales components enum.

    This is used to handle the supported components in scales.
    """

    COMMANDS = 'commands'
    INTERFACE = 'interface'
    UPLOAD = 'upload'

    def __new__(cls, value):
        if value in ScaleComponent:
            return value
        raise ValueError('%s is not a valid ScaleComponent' % value)


class Status(metaclass=IterableType):
    """Command status enum.

    This is used to handle the current status of scale commands.
    """

    ERROR = 'error'
    FAILED = 'failed'
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'

    def __new__(cls, value):
        if value in Status:
            return value
        raise ValueError('%s is not a valid Status' % value)
