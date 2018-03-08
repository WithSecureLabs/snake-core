# pylint: disable=missing-docstring

from snake.config import constants
from snake.scale import scale


__scale__ = scale(
    name='hashes',
    description='a module to calculate hashes on files',
    version=constants.VERSION,
    author="Countercept",
    supports=[
    ]
)
