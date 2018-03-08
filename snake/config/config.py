"""The configuration module.

This module contains all the classes and code in order to share configuration
information across snake.
"""

import sys
from os import path

import pkg_resources
import yaml

from snake import error
from snake.config import constants


class Config:
    """The config class passed around snake to share configuration variables.

    The config class should really only be instantiated once and then passed
    around as required by other files. This means that any updates to this
    object will be shared across without the need to restart snake.

    Attributes:
        scale_configs (dict): Configuration parameters for snake.
        snake_config (dict): Configuration parameters for snake scales.
    """

    def __init__(self, config_file=None):
        """Initialise the config object

        This will clear out the dictionaries and load in the base configuration
        for snake. If a configuration file is supplied this will be loaded
        'ontop' of the base configuration.

        Args:
            config_file (:obj:`str`, optional): The path to an external
                configuration file. Defaults to None.
        """
        self.scale_configs = {}
        self.snake_config = {}
        self.load_config(config_file)

    def load_config(self, config_file=None):
        """Load the snake configuration files.

        This loads the base configuration and along with an external
        configuration if supplied.

        Args:
            config_file (str, optional): The path to an external
                configuration file. Defaults to None.

        Raises:
            Exception: When any error occurs in loading a configuration from
            file.
        """
        # Load base
        config_path = pkg_resources.resource_filename("snake", "data/config/snake.conf")
        try:
            with open(config_path, 'rb') as stream:
                base_config = yaml.safe_load(stream)
            self.snake_config.update(base_config)
        except Exception as err:
            print("Failed to parse base config file: %s" % err)
            sys.exit(1)

        # If user specified config file then use that otherwise try and load
        # from etc config
        if config_file:
            if not path.exists(config_file):
                print("Not a valid config_file: %s" % config_file)
                sys.exit(1)
            try:
                with open(config_file, 'rb') as stream:
                    snake_config = yaml.safe_load(stream)
                self.snake_config.update(snake_config)
            except Exception as err:
                print("Failed to parse user config file: %s" % err)
                sys.exit(1)
        else:
            # /etc/snake
            etc_conf = path.join(path.abspath(path.expanduser(constants.ETC_DIR)), 'snake.conf')
            if path.exists(etc_conf):
                try:
                    etc_config = {}
                    with open(etc_conf, 'rb') as stream:
                        etc_config = yaml.safe_load(stream)
                    self.snake_config.update(etc_config)
                except Exception as err:
                    print("Failed to parse etc config file: %s" % err)
                    sys.exit(1)

    def load_scale_config(self, scale_name):
        """Load a scale configuration from file

        This loads the scale configuration files based on the scale name
        passed. It will load the base config along with the etc configuration
        if present.

        Args:
            scale_name (str): The name of the scale to load the configuration
            for.

        Raises:
            SnakeError: When the external configuration file fails to load.
        """
        self.scale_configs[scale_name] = {}
        # Load base if we need one
        config_path = pkg_resources.resource_filename("snake.scales.{}".format(scale_name), "{}.conf".format(scale_name))
        if path.exists(config_path):
            with open(config_path, 'rb') as stream:
                base_config = yaml.safe_load(stream)
            self.scale_configs[scale_name].update(base_config)

            # Try and load from etc config
            etc_conf = path.join(path.abspath(path.expanduser(constants.ETC_DIR)), "scales", "{}.conf".format(scale_name))
            if path.exists(etc_conf):
                try:
                    etc_config = {}
                    with open(etc_conf, 'rb') as stream:
                        etc_config = yaml.safe_load(stream)
                    if etc_config is None:  # The config file is empty this is fine
                        etc_config = {}
                    self.scale_configs[scale_name].update(etc_config)
                except Exception as err:
                    raise error.SnakeError('failed to load config: {}: {} - {}'.format(etc_conf, err.__class__, err))
