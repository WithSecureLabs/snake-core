# pylint: disable=missing-docstring

from snake.config import constants
from snake.scale import scale, FileType


__scale__ = scale(
    name='strings',
    description='a module to extract strings from files',
    version=constants.VERSION,
    author="Countercept",
    supports=[
        FileType.FILE
    ]
)
