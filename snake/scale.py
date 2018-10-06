"""The scale module.

This contains most if not all the code required to create a scale for snake.
"""

import abc
import copy
import functools
import importlib
import json as j
import logging
import pkgutil
import sys

from snake import enums
from snake import error
from snake import schema
from snake import utils
from snake.enums import FileType


# pylint: disable=too-few-public-methods


app_log = logging.getLogger("tornado.application")  # pylint: disable=invalid-name

__all__ = [
    "FileType"
]


class BaseOptions():
    """The base options class.

    This is the base options class used throughout scale components.

    Attributes:
        args (dict, optional): Valid arguments for a function. Defaults to None.
        info (str, optional): The information about a function. Defaults to 'No help available!'
        mime (str, optional): The mime restriction on the function. Defaults to None.
    """

    def __init__(self, args=None, info='No help available!', mime=None):
        self.args = {} if args is None or not args else args
        self.info = info
        self.mime = mime


class CommandOptions(BaseOptions):
    """Extends `BaseOptions`.

    Used for command functions in the command component.
    """
    pass


class PullOptions(BaseOptions):
    """Extends `BaseOptions`.

    Used for pull functions in the interface component.
    """
    pass


class PushOptions(BaseOptions):
    """Extends `BaseOptions`.

    Used for push functions in the interface component.
    """
    pass


class Commands(metaclass=abc.ABCMeta):
    """The command component.

    This is used to create a command component for a scale. The command
    component is used to run commands on a sample (it does what it says on the
    tin). The commands are run on the sample and the output is stored into the
    database in json format. Supporting functions can be created that will
    convert the json to additional formats if so desired.

    This class defines abstract functions that must be overriden in order for a
    scale to support a command component.

    Attributes:
        command_list (list): A list of all the command functions.
        snake (:obj:`Snake`): For use internally by snake. (Do not touch)!
    """

    class Snake:
        """A collection of private methods for use by snake.

        Attributes:
            __cmd (:obj:`Commands`): The parent `Commands` object.
        """

        def __init__(self, cmd):
            self.__cmd = cmd

        def __formats(self, cmd):
            """A list of supported formats for a command.

            This automatically finds the supporting formatting functions for a command.

            Args:
                cmd (str): The name of the command in question.

            Returns:
                list: The list of formatting functions for the command.
            """
            fmts = [enums.Format.JSON]
            for f in enums.Format:
                if f == enums.Format.JSON:
                    continue
                func = '{}_{}'.format(cmd, f)
                if hasattr(self.__cmd, func):
                    fmts += [f]
            return fmts

        def command(self, command_name):
            """Get a command function.

            Get the function for a given command name.

            Args:
                command_name (str): The name of the command to get.

            Returns:
                func: The command function requested.

            Raises:
                CommandError: If the command is not supported.
            """
            for i in self.__cmd.command_list:
                if i.__name__ == command_name:
                    return i
            raise error.CommandError('commands does not support command: {}'.format(command_name))

        def command_info(self, cmd):
            """Get the information for a command.

            This extracts and returns the 'useful' information for a command.

            Args:
                cmd (fun): The command function to extract the information from.

            Returns:
                dict: A dictionary containing the: name, args, formats, and info.
            """
            return {
                'command': cmd.__name__,
                'args': {k: v.to_dict() for k, v in cmd.cmd_opts.args.items()} if cmd.cmd_opts.args else None,
                'formats': self.__formats(cmd.__name__),
                'info': cmd.cmd_opts.info
            }

        def format(self, fmt, cmd, json):
            """Format a commands output.

            This formats the commands json output into a alternative but
            supported format. So if the command supports the requested format
            the json will be converted to this and returned. This never alters
            the data in the database.

            Args:
                fmt (str): The format to convert the output to.
                cmd (func): The command.
                json (str): The json to covert.

            Returns:
                str: The formatted output.

            Raises:
                TypeError: If the format is not supported by the enum.
            """
            if isinstance(json, bytes):
                json = j.loads(json.decode('utf-8'))
            if fmt not in enums.Format:
                raise TypeError('format not supported')
            if fmt == enums.Format.JSON:
                return json
            if fmt == enums.Format.MARKDOWN:
                func = '%s_markdown' % cmd
            elif fmt == enums.Format.PLAINTEXT:
                func = '%s_plaintext' % cmd
            else:
                raise TypeError('format not supported')

            if not hasattr(self.__cmd, func):
                raise TypeError('format not supported')
            if json is None:  # Running or pending
                return json
            if isinstance(json, dict) and 'error' in json:  # Handle error message formating
                if fmt == enums.Format.JSON:
                    return json
                if fmt == enums.Format.MARKDOWN:
                    return '**' + json['error'] + '**'
                elif fmt == enums.Format.PLAINTEXT:
                    return json['error']

            return self.__cmd.__getattribute__(func)(json)

        def info(self):
            """A list of information for commands.

            A list of dictionaries containing the information about all the supported commands.

            Returns:
                list: list of `command_info` dictionaries.
            """
            commands = []
            for cmd in self.__cmd.command_list:
                commands.append(self.command_info(cmd))
            return commands

    def __init__(self):
        self.check()
        self.command_list = []
        for i in dir(self):
            f = self.__getattribute__(i)
            if hasattr(f, '__command__'):
                self.command_list.append(f)
        if not self.command_list:
            raise error.CommandError('commands has no commands defined!')
        self.snake = self.Snake(self)

    @abc.abstractmethod
    def check(self):
        """The basic check command.

        This is used by snake to check if it can successfully run commands
        within the Commands component. If this check fails the component will
        fail.
        """
        pass


class Interface(metaclass=abc.ABCMeta):
    """The interface component.

    This is used to add interface support to a scale. An interface acts as a
    middleware layer between the user and another 3rd party api. In general no
    information is stored in snake and the queries are always live to the
    interfaced system, but cache can be used if required.

    This class defines abstract functions that must be overriden in order for a
    scale to support a interface component.

    Attributes:
        pull_list (list): A list of all the pull functions.
        push_list (list): A list of all the push functions.
        snake (:obj:`Snake`): For use internally by snake. (Do not touch)!
    """

    class Snake:
        """A collection of private methods for use by snake.

        Attributes:
            __intf (:obj:`Interface`): The parent `Interface` object.
        """

        def __init__(self, intf):
            self.__intf = intf

        def __formats(self, cmd):
            """A list of supported formats for a command.

            This automatically finds the supporting formatting functions for a command.

            Args:
                cmd (str): The name of the command in question.

            Returns:
                list: The list of formatting functions for the command.
            """
            fmts = [enums.Format.JSON]
            for f in enums.Format:
                if f == enums.Format.JSON:
                    continue
                func = '{}_{}'.format(cmd, f)
                if hasattr(self.__intf, func):
                    fmts += [f]
            return fmts

        def format(self, fmt, cmd, json):
            """Format a pull/push command output.

            This formats the commands json output into a alternative but
            supported format. So if the command supports the requested format
            the json will be converted to this and returned. This never alters
            the data in the database.

            Args:
                fmt (str): The format to convert the output to.
                cmd (func): The command.
                json (str): The json to covert.

            Returns:
                str: The formatted output.

            Raises:
                TypeError: If the format is not supported by the enum.
            """
            if fmt not in enums.Format:
                raise TypeError('format not supported')
            if fmt == enums.Format.JSON:
                return json
            if fmt == enums.Format.MARKDOWN:
                func = '%s_markdown' % cmd
            elif fmt == enums.Format.PLAINTEXT:
                func = '%s_plaintext' % cmd
            else:
                raise TypeError('format not supported')

            if not hasattr(self.__intf, func):
                raise TypeError('format not supported')
            return self.__intf.__getattribute__(func)(json)

        def info(self):
            """A dictionary of information for commands.

            A dictionary containing two lists of commands, one for pull, and one for push.

            Returns:
                dict: dictionary containing two list of `puller_info`/`pusher_info` dictionaries.
            """
            pullers = []
            pushers = []
            for i in self.__intf.pull_list:
                pullers.append(self.puller_info(i))
            for i in self.__intf.push_list:
                pushers.append(self.pusher_info(i))
            return {
                'pullers': pullers,
                'pushers': pushers
            }

        def puller(self, puller):
            """Get a pull command function.

            Get the function for a given command name.

            Args:
                puller (str): The name of the command to get.

            Returns:
                func: The command function requested.

            Raises:
                InterfaceError: If the command is not supported.
            """
            for i in self.__intf.pull_list:
                if i.__name__ == puller:
                    return i
            raise error.InterfaceError('interface does not support puller: %s' % puller)

        def puller_info(self, cmd):
            """Get the information for a pull command.

            This extracts and returns the 'useful' information for a pull command.

            Args:
                cmd (fun): The command function to extract the information from.

            Returns:
                dict: A dictionary containing the: command, args, formats, and info.
            """
            return {
                'command': cmd.__name__,
                'args': {k: v.to_dict() for k, v in cmd.pull_opts.args.items()} if cmd.pull_opts.args else None,
                'formats': self.__formats(cmd.__name__),
                'info': cmd.pull_opts.info
            }

        def pusher(self, pusher):
            """Get a push command function.

            Get the function for a given command name.

            Args:
                pusher (str): The name of the command to get.

            Returns:
                func: The command function requested.

            Raises:
                InterfaceError: If the command is not supported.
            """
            for i in self.__intf.push_list:
                if i.__name__ == pusher:
                    return i
            raise error.InterfaceError('interface does not support pusher: %s' % pusher)

        def pusher_info(self, cmd):
            """Get the information for a push command.

            This extracts and returns the 'useful' information for a push command.

            Args:
                cmd (fun): The command function to extract the information from.

            Returns:
                dict: A dictionary containing the: command, args, formats, and info.
            """
            return {
                'command': cmd.__name__,
                'args': {k: v.to_dict() for k, v in cmd.push_opts.args.items()} if cmd.push_opts.args else None,
                'formats': self.__formats(cmd.__name__),
                'info': cmd.push_opts.info
            }

    def __init__(self):
        self.check()
        self.pull_list = []
        self.push_list = []
        for i in dir(self):
            f = self.__getattribute__(i)
            if hasattr(f, '__pull__') and f.__pull__:
                self.pull_list.append(f)
            elif hasattr(f, '__push__') and f.__push__:
                self.push_list.append(f)
        self.snake = self.Snake(self)

    @abc.abstractmethod
    def check(self):
        """The basic check command.

        This is used by snake to check if it can successfully run commands
        within the Interface component. If this check fails the component will
        fail.
        """
        pass


class Scale:  # pylint: disable=too-many-instance-attributes
    """A snake scale.

    The class required to create a scale. This should never be subclassed just
    called with the correct attributes.

    Attributes:
        name (str): name of scale.
        description (str): description of scale.
        version (str): version number.
        author (str): author of scale.
        supports (list): supported file types (`FileType`).

    """
    def __init__(self, attrs):
        if 'name' not in attrs:
            raise error.ScaleError('scale requires name field')
        if 'description' not in attrs:
            raise error.ScaleError('scale requires description field')
        if 'version' not in attrs:
            raise error.ScaleError('scale requires version field')
        if 'author' not in attrs:
            raise error.ScaleError('scale requires author field')

        self.name = attrs['name']
        self.description = attrs['description']
        self.version = attrs['version']
        self.author = attrs['author']
        self.supports = attrs['supports'] if 'supports' in attrs and attrs['supports'] else [x for x in enums.FileType]

        self.components = {}

        self.caveats = attrs['caveats'] if 'caveats' in attrs else None  # TODO: Remove

        self.scale_requires = attrs['scale_requires'] if 'scale_requires' in attrs else None  # TODO: Remove
        self.system_requires = attrs['system_requires'] if 'system_requires' in attrs else None  # TODO: Remove

    def info(self):
        """Scale information.

        Reports information about the scale, usually just the attibutes defined
        on the scale.

        Returns:
            dict: A dictionary of information about the scale.
        """
        dictionary = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "supports": self.supports,
            "components": [x for x in self.components]
        }
        return dictionary

    def load_components(self):
        """Load the scales components.

        This searches through the scales folder and attempts to import its components.

        Raises:
            Exception: when any error occurs that is not a scale based error.
        """
        # A little bit assumptive but we can get the already imported module in
        # order to parse its components
        mod = sys.modules.get("snake.scales.{}".format(self.name))
        if not mod:
            raise error.ScaleError("failed to locate module: snake.scales.{}".format(self.name))
        for _imp, mod_name, _is_pkg in pkgutil.iter_modules(mod.__path__):
            if mod_name == 'commands':
                try:
                    cmd = importlib.import_module('snake.scales.' + self.name + '.commands')
                    if hasattr(cmd, 'Commands'):
                        self.components['commands'] = cmd.Commands()
                except error.ScaleError as err:  # TODO: Handle warnings somehow?
                    app_log.error('%s: %s', self.name, err)
                except Exception as err:
                    raise err
            if mod_name == 'interface':
                try:
                    intf = importlib.import_module('snake.scales.' + self.name + '.interface')
                    if hasattr(intf, 'Interface'):
                        self.components['interface'] = intf.Interface()
                except error.ScaleError as err:  # TODO: Handle warnings somehow?
                    app_log.error('%s: %s', self.name, err)
                except Exception as err:
                    raise err

            if mod_name == 'upload':
                try:
                    upld = importlib.import_module('snake.scales.' + self.name + '.upload')
                    if hasattr(upld, 'Upload'):
                        self.components['upload'] = upld.Upload()
                except error.ScaleError as err:  # TODO: Handle warnings somehow?
                    app_log.error('%s: %s', self.name, err)
                except Exception as err:
                    raise err


class Upload(metaclass=abc.ABCMeta):
    """The upload component.

    This is used to add upload support to a scale. This component allows snake
    to learn new ways to ingest files.

    This class defines abstract functions that must be overriden in order for a
    scale to support a upload component.

    Attributes:
        snake (:obj:`Snake`): For use internally by snake. (Do not touch)!
    """

    class Snake:
        """A collection of private methods for use by snake.

        Attributes:
            __upld (:obj:`Upload`): The parent `Upload` object.
        """

        def __init__(self, upld):
            self.__upld = upld

        def info(self):
            """Information about the uploader.

            This presents the information about the upload component.

            Returns:
                dict: information about upload.
            """
            return {
                'args': {k: type(v).__name__ for k, v in self.__upld.arguments().items()} if self.__upld.arguments() else None,
                'info': self.__upld.info()
            }

    def __init__(self):
        self.snake = self.Snake(self)

    @abc.abstractmethod
    def arguments(self):
        """Supported arguments to upload.

        Returns:
            dict: A dictionary of supported arguments.
        """
        pass

    @abc.abstractmethod
    def info(self):
        """Information about the uploader.

        Returns:
            str: Information about the upload component.
        """
        pass

    @abc.abstractmethod
    def upload(self, args, working_dir):
        """The upload function.

        This handles the custom uploader so that snake can ingest.

        Note:
            This must drop a file into the `working_dir` and return the name of the file dropped.

        Args:
            args (dict): The populated arguments built from `arguments`.
            working_dir (str): Path to the working directory.

        Returns:
            str: The name of the file dropped into the working_dir.
        """
        pass


# TODO: Allow decorator without args...
def autorun(func):
    """Commands: Autorun decorator.

    This is used to flag a command as an autorun. A function decorated with
    this depending on mime will be automatically executed when a file is
    uploaded to snake.

    Returns:
        func: The autorun enabled function.
    """
    func.__autorun__ = True
    return func


def command(cmd_dict=None):
    """Commands: Command decorator.

    Marks a function as a command function.

    Note:
        The following prototype must be followed:
            func(self, args, file, opts)

    Args:
        cmd_dict (:obj:`CommandOptions`, optional): The additional information for a command.

    Returns:
        func: The wrapped command function.
    """
    def decorator(func):
        """Decorates the function."""
        # Load the attached dictionary if there is one, otherwise create
        # the default
        if cmd_dict:
            cmd_opts = CommandOptions(**cmd_dict)
        else:
            cmd_opts = CommandOptions()
        func.cmd_opts = cmd_opts

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            """Wraps the function."""
            if args and 'args' in kwargs:
                raise TypeError("%s got multiple values for argument 'args'" % func.__name__)
            elif 'args' in kwargs:
                args_ = kwargs['args']
            else:
                args_ = args[0]
            if len(args) > 1 and 'sha256_digest' in kwargs:
                raise TypeError("%s got multiple values for argument 'sha256_digest'" % func.__name__)
            elif 'sha256_digest' in kwargs:
                file_storage = utils.FileStorage(kwargs['sha256_digest'])
            else:
                file_storage = utils.FileStorage(args[1])
            opts = func.cmd_opts

            if cmd_opts.args.keys():
                args_ = schema.Schema(fields=copy.deepcopy(cmd_opts.args)).load(args_)

            self.check()

            output = func(args=args_, file=file_storage, opts=opts, self=self)
            if not isinstance(output, dict) and not isinstance(output, list):
                raise TypeError("%s failed to return a dictionary or list" % func.__name__)
            return output
        wrapper.__wrapped__ = func
        wrapper.__command__ = True
        if not hasattr(wrapper, '__autorun__'):
            wrapper.__autorun__ = False
        return wrapper
    return decorator


def pull(pull_dict=None):
    """Interface: Pull decorator.

    Marks a function as a pull command function.

    Note:
        The following prototype must be followed:
            func(self, args, file, opts)

    Args:
        pull_dict (:obj:`PullOptions`, optional): The additional information for a command.

    Returns:
        func: The wrapped command function.
    """
    def decorator(func):
        """Decorates the function."""
        # Load the attached dictionary if there is one, otherwise create
        # the default
        if pull_dict:
            pull_opts = PullOptions(**pull_dict)
        else:
            pull_opts = PullOptions()
        func.pull_opts = pull_opts

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            """Wraps the function."""
            if args and 'args' in kwargs:
                raise TypeError("%s got multiple values for argument 'args'" % func.__name__)
            elif 'args' in kwargs:
                args_ = kwargs['args']
            else:
                args_ = args[0]
            if len(args) > 1 and 'sha256_digest' in kwargs:
                raise TypeError("%s got multiple values for argument 'sha256_digest'" % func.__name__)
            elif 'sha256_digest' in kwargs:
                file_storage = utils.FileStorage(kwargs['sha256_digest'])
            else:
                file_storage = utils.FileStorage(args[1])
            opts = func.pull_opts

            if pull_opts.args.keys():
                args_ = schema.Schema(fields=copy.deepcopy(pull_opts.args)).load(args_)

            self.check()

            output = func(args=args_, file=file_storage, opts=opts, self=self)
            if not isinstance(output, dict) and not isinstance(output, list):
                raise TypeError("%s failed to return a dictionary or list" % func.__name__)
            return output
        wrapper.__wrapped__ = func
        wrapper.__pull__ = True
        return wrapper
    return decorator


def push(push_dict=None):
    """Interface: Push decorator.

    Marks a function as a push command function.

    Note:
        The following prototype must be followed:
            func(self, args, file, opts)

    Args:
        push_dict (:obj:`PushOptions`, optional): The additional information for a command.

    Returns:
        func: The wrapped command function.
    """
    def decorator(func):
        """Decorates the function."""
        # Load the attached dictionary if there is one, otherwise create
        # the default
        if push_dict:
            push_opts = PushOptions(**push_dict)
        else:
            push_opts = PushOptions()
        func.push_opts = push_opts

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            """Wraps the function."""
            if args and 'args' in kwargs:
                raise TypeError("%s got multiple values for argument 'args'" % func.__name__)
            elif 'args' in kwargs:
                args_ = kwargs['args']
            else:
                args_ = args[0]
            if len(args) > 1 and 'sha256_digest' in kwargs:
                raise TypeError("%s got multiple values for argument 'sha256_digest'" % func.__name__)
            elif 'sha256_digest' in kwargs:
                file_storage = utils.FileStorage(kwargs['sha256_digest'])
            else:
                file_storage = utils.FileStorage(args[1])
            opts = func.push_opts

            if push_opts.args.keys():
                args_ = schema.Schema(fields=copy.deepcopy(push_opts.args)).load(args_)

            self.check()

            output = func(args=args_, file=file_storage, opts=opts, self=self)
            if not isinstance(output, dict) and not isinstance(output, list):
                raise TypeError("%s failed to return a dictionary or list" % func.__name__)
            return output
        wrapper.__wrapped__ = func
        wrapper.__push__ = True
        return wrapper
    return decorator


def scale(**attrs):
    """Scale creation function.

    This is used to create a scale, with the correct attributes.

    Returns:
        :obj:`Scale`: An initialised scale.
    """
    return Scale(attrs)
