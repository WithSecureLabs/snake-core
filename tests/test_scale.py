import pytest

from snake import scale
from snake.error import ScaleError


def test_command_decorator():
    """
    Test the command decorator
    """

    def f(args, file, opts):  # pylint: disable=unused-argument
        return 'abcd'

    # Check no cmd_opts
    cmd = scale.command()(f)
    assert cmd.__command__ is True
    assert cmd.__wrapped__ is f
    assert isinstance(cmd.cmd_opts, scale.CommandOptions)
    # assert cmd(None, None, None) is 'abcd'

    # Check cmd_opts
    cmd = scale.command({})(f)
    assert cmd.__command__ is True
    assert cmd.__wrapped__ is f
    assert isinstance(cmd.cmd_opts, scale.CommandOptions)
    # assert cmd(None, None, None) is 'abcd'

    # Check invalid cmd_opts
    with pytest.raises(TypeError):
        cmd = scale.command({'invalid': None})(f)


def test_scales():
    """
    Test the Module class
    """

    # TODO: Assert mandatory
    with pytest.raises(ScaleError):
        mod = scale.Scale({})

    mod = scale.Scale({
        'name': 'abcd',
        'description': '1234',
        'author': '1234',
        'version': '1.0',
        'supports': [
            'binary',
            'memory'
        ]
    })
    assert mod.name == 'abcd'
    assert len(mod.components.keys()) is 0
    assert mod.description == '1234'
    assert mod.author == '1234'
    assert mod.version == '1.0'
    assert mod.supports == ['binary', 'memory']

    assert mod.info() == {
        "name": mod.name,
        "description": mod.description,
        "author": mod.author,
        "version": mod.version,
        "components": [],
        "supports": mod.supports
    }


def test_command_options():
    """
    Test the CommandOptions class
    """

    cmd_opts = scale.CommandOptions()
    assert cmd_opts.args == {}
    assert cmd_opts.info == 'No help available!'
    assert cmd_opts.mime is None


def test_commands():
    """
    Test the Commands class
    """

    with pytest.raises(TypeError):
        scale.Commands()  # pylint: disable=abstract-class-instantiated

    class Commands(scale.Commands):
        def check(self):
            pass

        @scale.command()
        def test(self, args, file, opts):  # pylint: disable=unused-argument, no-self-use
            return 'abcd'

    cmds = Commands()
    assert cmds.snake.info() == [{
        'command': 'test',
        'args': None,
        'info': 'No help available!',
        'formats': ['json']
    }]
    assert cmds.snake.command('test').__name__ == 'test'
