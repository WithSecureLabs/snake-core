# pylint: disable=missing-docstring

from snake.config import constants
from snake.scale import scale


__scale__ = scale(
    name='url',
    description='a module to upload files to Snake from arbitrary URLs',
    version=constants.VERSION,
    author="Countercept",
    supports=[
    ]
)
