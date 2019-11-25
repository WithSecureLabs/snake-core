"""The markdown module."""

# pylint: disable=invalid-name


def bold(text):
    """Bold.

    Args:
        text (str): text to make bold.

    Returns:
        str: bold text.
    """
    return '**' + text + '**'


def code(text, inline=False, lang=''):
    """Code.

    Args:
        text (str): text to make code.
        inline (bool, optional): format as inline code, ignores the lang argument. Defaults to False.
        lang (str, optional): set the code block language. Defaults to ''.

    Returns:
        str: code text.
    """
    if inline:
        return '`{}`'.format(text)
    return '```{}\r\n'.format(lang) + text + '\r\n```'


def cr():
    """Carriage Return (Line Break).

    Returns:
        str: Carriage Return.
    """
    return '\r\n'


def h1(text):
    """Heading 1.

    Args:
        text (str): text to make heading 1.

    Returns:
        str: heading 1 text.
    """
    return '# ' + text + '\r\n'


def h2(text):
    """Heading 2.

    Args:
        text (str): text to make heading 2.

    Returns:
        str: heading 2 text.
    """
    return '## ' + text + '\r\n'


def h3(text):
    """Heading 3.

    Args:
        text (str): text to make heading 3.

    Returns:
        str: heading 3 text.
    """
    return '### ' + text + '\r\n'


def h4(text):
    """Heading 4.

    Args:
        text (str): text to make heading 4.

    Returns:
        str: heading 4 text.
    """
    return '#### ' + text + '\r\n'


def newline():
    """New Line.

    Returns:
        str: New Line.
    """
    return '\r\n'


def paragraph(text):
    """Paragraph.

    Args:
        text (str): text to make into a paragraph.

    Returns:
        str: paragraph text.
    """
    return text + '\r\n'


def sanitize(text):
    """Sanitize text.

    This attempts to remove formatting that could be mistaken for markdown.

    Args:
        text (str): text to sanitise.

    Returns:
        str: sanitised text.
    """
    if '```' in text:
        text = text.replace('```', '(3xbacktick)')

    if '|' in text:
        text = text.replace('|', '(pipe)')

    if '_' in text:
        text = text.replace('_', r'\_')

    return text


def table_header(columns=None):
    """Table header.

    Creates markdown table headings.

    Args:
        text (tuple): column headings.

    Returns:
        str: markdown table header.
    """
    line_1 = '|'
    line_2 = '|'
    for c in columns:
        line_1 += ' ' + c + ' |'
        line_2 += ' --- |'
    line_1 += '\r\n'
    line_2 += '\r\n'
    return line_1 + line_2


def table_row(columns=None):
    """Table row.

    Creates markdown table row.

    Args:
        text (tuple): column data.

    Returns:
        str: markdown table row.
    """
    row = '|'
    for c in columns:
        row += ' ' + c + ' |'
    row += '\r\n'
    return row


def url(text, url_):
    """Url

    Args:
        text (str): text for url.
        url (str): url for text.

    Returns:
        str: url.
    """
    return '[' + text + '](' + url_ + ')'
