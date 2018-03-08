"""This module exposes the initialised config object.

Attributes:
    config_parser (:obj:`Config`): The configuration parser for snake.
    scale_configs (dict): Convenient access to the scale_configs dictionary.
    snake_config (dict): Convenient access to the snake_config dictionary.
"""
from snake.config import config

# pylint: disable=invalid-name

config_parser = config.Config()
scale_configs = config_parser.scale_configs
snake_config = config_parser.snake_config
