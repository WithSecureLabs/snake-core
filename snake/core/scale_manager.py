"""The scale manager module.

This module provides scale management, it does all things scales. i.e. it is
responsible for loading, storing and providing access to scales.
"""

import logging
import os
import pkgutil
import sys
from importlib import util

import pkg_resources

from snake import enums
from snake import error
from snake import scales as core_scales
from snake.config import config_parser
from snake.config import snake_config


app_log = logging.getLogger("tornado.application")  # pylint: disable=invalid-name


class ScaleManager():
    """The scale manager.

    This managers everything to do with scales to make life easier in other parts of snake.

    Attributes:
        scales (dict): A dictionary of loaded scales.
    """

    def __init__(self, scales=None):
        """Initialise the scale manager.

        Attempts to load in all installed scales, and will gracefully handle
        any errors encountered when trying to load a scale and present it in
        the log.

        Args:
            scales (list, optional): A list of specific scales to load. Defaults to None.
        """
        self.scales = {}
        self.__load_scales(scales)

    def __load_scale(self, scale_name, scale_path):
        """Load a scale.

        Will attempt to load in a scale. It is added to the scale dictionary on success.

        Note:
            A scale with the same name as another will be replaced.

        Args:
            scale_name (str): The scale to load.
            scale_path (str): The path to the scale's __init__.py.

        Raises:
            SnakeError: When scale fails to load.
            ImportError: When a scale fails to import.
        """
        try:
            namespace = "snake.scales.{}".format(scale_name)
            spec = util.spec_from_file_location(namespace, scale_path)
            mod = util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            sys.modules[namespace] = mod  # Allow for import by name
            config_parser.load_scale_config(scale_name)  # TODO: Handle me better?!
            scale = mod.__scale__
            scale.load_components()
            self.scales[scale_name] = scale
        except error.SnakeError as err:
            app_log.error('%s - %s', scale_name, err)
        except ImportError as err:
            app_log.error('%s - %s', scale_name, err)

    def __load_scales(self, scales=None):
        """Load scales.

        Loads the scales using all three supported methods. This will load the
        core scales, followed by the pip installed scales, and wrapped up by
        loading an user specified scales.

        Notes:
            An empty list will result in no scales being loaded.

        Args:
            scales (list, optional): A list of specific scales to load. Defaults to None.
        """
        # Core
        for _imp, mod_name, is_pkg in pkgutil.iter_modules(core_scales.__path__):
            if is_pkg:
                if isinstance(scales, list) and mod_name not in scales:
                    continue
                scale_path = os.path.join(core_scales.__path__[0], mod_name)
                self.__load_scale(mod_name, os.path.join(scale_path, "__init__.py"))

        # Pip
        for entry_point in pkg_resources.iter_entry_points(group='snake.scales'):
            if isinstance(scales, list) and entry_point.name not in scales:
                continue
            loader = pkgutil.get_loader(entry_point.module_name)
            self.__load_scale(entry_point.name, loader.path)

        # User
        for directory in snake_config['snake_scale_dirs']:
            directory = os.path.abspath(os.path.expanduser(directory))
            if not os.path.isdir(directory):
                app_log.error("snake scale directory provided is not a directory: %s", directory)
                continue
            # Get the first layer of directories and give these to `iter_modules`
            scale_dirs = [os.path.join(directory, x) for x in os.listdir(directory) if os.path.isdir(os.path.join(directory, x))]
            for imp, mod_name, is_pkg in pkgutil.iter_modules(scale_dirs):
                if is_pkg:
                    if isinstance(scales, list) and mod_name not in scales:
                        continue
                    scale_path = os.path.join(imp.path, mod_name)
                    self.__load_scale(mod_name, os.path.join(scale_path, "__init__.py"))

    # General
    @staticmethod
    def get_component(scale, component):
        """Gets the component for a scale.

        This will return the specified component for the given scale if supported.

        Args:
            scale (:obj:`Scale`): The scale.
            component (:obj:`ScaleComponent`): The component to get.

        Returns:
            obj: The requested component.

        Raises:
            ScaleError: If the component is not supported or provided.
        """
        if component == enums.ScaleComponent.COMMANDS:
            if component not in scale.components:
                raise error.ScaleError("scale does not provide commands: %s" % scale.name)
            return scale.components[enums.ScaleComponent.COMMANDS]
        if component == enums.ScaleComponent.INTERFACE:
            if component not in scale.components:
                raise error.ScaleError("scale does not provide interface: %s" % scale.name)
            return scale.components[enums.ScaleComponent.INTERFACE]
        if component == enums.ScaleComponent.UPLOAD:
            if component not in scale.components:
                raise error.ScaleError("scale does not provide upload: %s" % scale.name)
            return scale.components[enums.ScaleComponent.UPLOAD]
        raise error.ScaleError("component is not supported")

    def get_scale(self, scale, file_type=None):
        """Get a scale.

        Gets the scale for a given name. If the `file_type` is given then scales will be restricted to those supported.

        Args:
            scale (str): The name of the scale.
            file_type (:obj:`FileType`, optional): The type of the file. Defaults to None.

        Returns:
            `Scale`: The requested scale.

        Raises:
            ScaleError: If it is not supported for the given `FileType` or if the scale is not found.
        """
        if scale in self.scales.keys():
            _scale = self.scales[scale]
            if file_type and _scale.supports and file_type not in _scale.supports:
                raise error.ScaleError("scale does not support file type: %s" % file_type)
            return _scale
        raise error.ScaleError('scale not found')

    def get_scales(self, file_type=None):
        """Get scales information.

        Gets the information about all loaded scales. If the `file_type` is
        given then any unsupported scales are ignored.

        Args:
            file_type (:obj:`FileType`, optional): The type of the file. Defaults to None.

        Returns:
            list: A list dictionaries containing scale information.
        """
        scales = []
        for _, v in self.scales.items():
            if file_type and v.supports and file_type not in v.supports:
                continue
            scales += [v.info()]
        return scales

    def reload_scales(self):
        """Reloads the scales.

        Just calls `__load_scales` to reload them.
        """
        self.__load_scales()

    # Command

    def get_autoruns(self, file_type=None):
        """Get autoruns.

        Gets all autorun commands. If the `file_type` is given then this is
        restricted to those supported.

        Args:
            file_type (:obj:`FileType`, optional): The type of the file. Defaults to None.

        Returns:
            list: A list of autorun tuples (scale, command, mime).
        """
        autoruns = []
        for k, v in self.scales.items():
            if enums.ScaleComponent.COMMANDS not in v.components:
                continue
            if file_type and v.supports and file_type not in v.supports:
                continue
            cmd = v.components['commands']
            for i in cmd.command_list:
                if i.__autorun__:
                    autoruns += [(k, i.__name__, i.cmd_opts.mime)]
        return autoruns

    # Interface
    @staticmethod
    def get_interface_command(interface, interface_type, command):
        """Get interface command.

        Gets the command from an interface, these are either push or pull based commands.

        Args:
            interface (:obj:`Interface`): The interface.
            interface_type (:obj:`InterfaceType`): The interface command type.
            command (str): The command.

        Returns:
            func: The requested command.
        """
        i_type = enums.InterfaceType(interface_type)
        if i_type == enums.InterfaceType.PULL:
            return interface.snake.puller(command)
        if i_type == enums.InterfaceType.PUSH:
            return interface.snake.pusher(command)
        return None  # XXX: Should never get here.

    # Upload
    # None
