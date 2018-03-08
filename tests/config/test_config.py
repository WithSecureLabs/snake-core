import pytest

from snake import error
from snake.config import config
from snake.config import constants


# pylint: disable=too-many-statements


def test_config(mocker):
    """
    Test the Config class
    """

    def blank_file(*args, **kwargs):  # pylint: disable=unused-argument
        return './tests/files/blank.conf'

    def invalid_file(*args, **kwargs):  # pylint: disable=unused-argument
        return './tests/files/invalid.conf'

    def load_config_fake(self, config_file):  # pylint: disable=unused-argument
        pass

    def resource_filename_snake(self, config_file):  # pylint: disable=unused-argument
        return './snake/data/config/snake.conf'

    def resource_filename(package_or_requirement, resource_name):  # pylint: disable=unused-argument
        return './tests/files/test.conf'

    def resource_filename_err(package_or_requirement, resource_name):  # pylint: disable=unused-argument
        return './tests/files/test_fail.conf'

    # Test initialisation
    Config = config.Config  # pylint: disable=invalid-name
    load_config = Config.load_config
    Config.load_config = load_config_fake  # Monkey patch
    cfg = Config()
    assert len(cfg.scale_configs.keys()) is 0
    assert len(cfg.snake_config.keys()) is 0

    # Test full initialisation, but lazily
    Config.load_config = load_config  # Un-Monkey patch
    cfg = Config()
    assert len(cfg.scale_configs.keys()) is 0
    assert len(cfg.snake_config.keys()) is not 0

    # Test custom load file
    cfg = Config(config_file='./tests/files/test.conf')
    assert len(cfg.scale_configs.keys()) is 0
    assert len(cfg.snake_config.keys()) is not 0

    # Test snake load scale file
    mocker.patch('pkg_resources.resource_filename', resource_filename)
    cfg = Config()
    cfg.load_scale_config('test')
    assert len(cfg.scale_configs.keys()) is not 0
    assert len(cfg.snake_config.keys()) is not 0

    # Cause load_config to fail
    mocker.patch('pkg_resources.resource_filename', resource_filename_err)
    with pytest.raises(SystemExit):
        cfg = Config()

    # Remove patch
    mocker.stopall()

    # Pass missing config file
    with pytest.raises(SystemExit):
        cfg = Config(config_file='./tests/files/test_fail.conf')

    # Fake etc to test ETC support
    constants.ETC_DIR = './tests/files'

    # Test ETC_DIR config loading
    cfg = Config()
    assert len(cfg.scale_configs.keys()) is 0
    assert len(cfg.snake_config.keys()) is not 0

    # Test ETC_DIR failed config loading
    mocker.patch('os.path.join', blank_file)
    with pytest.raises(SystemExit):
        cfg = Config()
    mocker.stopall()

    # Test ETC_DIR blank config loading for scale
    cfg = Config()
    mocker.patch('os.path.join', blank_file)
    mocker.patch('pkg_resources.resource_filename', resource_filename)
    cfg.load_scale_config('test')
    assert len(cfg.scale_configs.keys()) is not 0
    assert len(cfg.snake_config.keys()) is not 0
    mocker.stopall()

    # Test ETC_DIR invalid config loading for scale
    cfg = Config()
    mocker.patch('os.path.join', invalid_file)
    mocker.patch('pkg_resources.resource_filename', resource_filename)
    with pytest.raises(error.SnakeError):
        cfg.load_scale_config('test')
    assert len(cfg.scale_configs.keys()) is not 0
    assert len(cfg.snake_config.keys()) is not 0
