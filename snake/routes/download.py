""" The download route module.

Attributes:
    DownloadRoute (tuple): The DownloadRoute.
"""

from snake.core import snake_handler
from snake.db import async_file_collection
from snake.utils import file_storage as fs


# pylint: disable=abstract-method
# pylint: disable=arguments-differ


class DownloadHandler(snake_handler.SnakeHandler):
    """Extends `SnakeHandler`."""

    async def get(self, sha256_digest):
        document = await async_file_collection.select(sha256_digest)
        if not document:
            self.write_warning("download - no sample for given sha256 digest", 404, sha256_digest)
            self.finish()
            return
        file_storage = fs.FileStorage(sha256_digest)
        buf_size = 4096
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename="' + document['name'] + '.inactive"')
        with open(file_storage.file_path, 'rb') as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                self.write(data)
        self.finish()


DownloadRoute = (r"/download/(?P<sha256_digest>[a-zA-Z0-9]+)?", DownloadHandler)  # pylint: disable=invalid-name
