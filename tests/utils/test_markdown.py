from snake.utils import markdown as md


def test_bold():
    """
    Test bold function
    """

    output = md.bold('abcd')
    assert output == '** abcd **'


def test_code():
    """
    Test code function
    """

    output = md.code('abcd')
    assert output == '```\r\nabcd\r\n```'


def test_cr():
    """
    Test cr function
    """

    output = md.cr()
    assert output == '\r\n'


def test_h1():
    """
    Test h1 function
    """

    output = md.h1('abcd')
    assert output == '# abcd\r\n'


def test_h2():
    """
    Test h2 function
    """

    output = md.h2('abcd')
    assert output == '## abcd\r\n'


def test_h3():
    """
    Test h3 function
    """

    output = md.h3('abcd')
    assert output == '### abcd\r\n'


def test_h4():
    """
    Test h4 function
    """

    output = md.h4('abcd')
    assert output == '#### abcd\r\n'


def test_newline():
    """
    Test newline function
    """

    output = md.newline()
    assert output == '\r\n'


def test_paragraph():
    """
    Test paragraph function
    """

    output = md.paragraph('abcd')
    assert output == 'abcd\r\n'


def test_sanitize():
    """
    Test sanitize function
    """

    output = md.sanitize('```')
    assert output == '(3xbacktick)'

    output = md.sanitize('|')
    assert output == '(pipe)'

    output = md.sanitize('_')
    assert output == r'\_'


def test_table_header():
    """
    Test table_header function
    """

    output = md.table_header(('a', 'b'))
    assert output == '| a | b |\r\n| --- | --- |\r\n'


def test_table_row():
    """
    Test table_row function
    """

    output = md.table_row(('a', 'b'))
    assert output == '| a | b |\r\n'


def test_url():
    """
    Test url function
    """

    output = md.url('a', 'b')
    assert output == '[a](b)'
