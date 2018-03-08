"""The module that supplies router management.

Currently this only hosts one function that is used to centralise the
generation of routes.
"""


def generate_routes():  # pylint: disable=too-many-locals
    """Generate a list of routes.

    Returns:
        list: The list of API routes.
    """
    # Only load them on generation
    from snake.routes import api
    from snake.routes import command
    from snake.routes import download
    from snake.routes import file
    from snake.routes import memory
    from snake.routes import scale
    from snake.routes import note
    from snake.routes import store
    from snake.routes import upload

    routes = [
        api.APIRoute,
        command.CommandRoute, command.CommandsRoute,
        download.DownloadRoute,
        file.FileRoute, file.FilesRoute, file.FileHexRoute,
        memory.MemoryRoute, memory.MemoriesRoute,
        scale.ScaleRoute, scale.ScaleCommandsRoute, scale.ScaleInterfaceRoute, scale.ScaleUploadRoute, scale.ScalesRoute,
        note.NoteRoute, note.NotePostRoute, note.NotesRoute,
        store.StoreRoute,
        upload.UploadFileRoute, upload.UploadFilesRoute, upload.UploadMemoryRoute
    ]

    return routes
