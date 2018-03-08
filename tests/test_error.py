import pytest

from snake import error


def test_snake_error():
    """
    Test the class SnakeError
    """
    with pytest.raises(TypeError):
        error.SnakeError()  # pylint: disable=no-value-for-parameter

    err = error.SnakeError('hello')
    assert 'hello' in err.message
    assert None is err.status_code
    assert None is err.payload

    err = error.SnakeError('hello', 500)
    assert 'hello' in err.message
    assert 500 is err.status_code
    assert None is err.payload

    err = error.SnakeError('hello', 500, 'extra')
    assert 'hello' in err.message
    assert 500 is err.status_code
    assert 'extra' is err.payload


def test_command_error():
    """
    Test the class CommandError
    """
    err = error.CommandError('hello')
    assert 'hello' in err.message
    assert err.status_code == 500
    assert None is err.payload


def test_scale_error():
    """
    Test the class CommandError
    """
    err = error.ScaleError('hello')
    assert 'hello' in err.message
    assert err.status_code == 500
    assert None is err.payload


def test_mongo_error():
    """
    Test the class CommandError
    """
    err = error.MongoError('hello')
    assert 'hello' in err.message
    assert err.status_code == 500
    assert None is err.payload


def test_server_error():
    """
    Test the class CommandError
    """
    err = error.ServerError('hello')
    assert 'hello' in err.message
    assert err.status_code == 500
    assert None is err.payload
