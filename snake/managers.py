"""The managers module.

This contains all instantiated managers for uses around snake.


Attributes:
    scale_manager (:obj:`ScaleManager`): The scale manager.
"""

from snake.core import scale_manager

scale_manager = scale_manager.ScaleManager()  # pylint: disable=invalid-name
