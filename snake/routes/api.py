""" The API route module.

Attributes:
    APIRoute (tuple): The APIRoute.
"""

from snake.config import constants
from snake.core import snake_handler


# pylint: disable=abstract-method
# pylint: disable=arguments-differ


class APIHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    async def get(self):
        self.jsonify({'api_version': constants.API_VERSION})
        self.finish()


APIRoute = (r"/api", APIHandler)  # pylint: disable=invalid-name
