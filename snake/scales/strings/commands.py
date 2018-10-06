# pylint: disable=missing-docstring
# pylint: disable=no-self-use
# pylint: disable=unused-argument

import shutil
import subprocess

from snake import error
from snake import fields
from snake import scale
from snake.scales.strings import regex


SPECIAL_CHARS = [" ", "'", '(', '"', '|', '&', '<', '`', '!', '>', ';', '$', ')', '\\\\']


class Commands(scale.Commands):
    def check(self):
        strings = shutil.which('strings')
        if not strings:
            raise error.CommandWarning("Binary 'strings' not found")
        return

    @scale.command({
        'info': 'This function will return strings found within the file'
    })
    def all_strings(self, args, file, opts):
        return str(subprocess.check_output(["strings", file.file_path]), encoding="utf-8").split('\n')

    @staticmethod
    def all_strings_plaintext(json):
        return '\n'.join(json)

    @scale.command({
        'args': {
            'min_length': fields.Int(default=5)
        },
        'info': 'This function will return interesting strings found within the file'
    })
    def interesting(self, args, file, opts):
        strings = str(subprocess.check_output(["strings", file.file_path]), encoding="utf-8").split('\n')
        min_length = args['min_length']
        output = []
        for string in strings:
            rules = []
            match = regex.IPV4_REGEX.search(string)
            if match and len(match.group()) > min_length:
                rules += ['IPV4_REGEX']
            match = regex.IPV6_REGEX.search(string)
            if match and len(match.group()) > min_length:
                rules += ['IPV6_REGEX']
            match = regex.EMAIL_REGEX.search(string)
            if match and len(match.group()) > min_length:
                rules += ['EMAIL_REGEX']
            match = regex.URL_REGEX.search(string)
            if match and len(match.group()) > min_length:
                rules += ['URL_REGEX']
            match = regex.DOMAIN_REGEX.search(string)
            if match and len(match.group()) > min_length:
                rules += ['DOMAIN_REGEX']
            match = regex.WINDOWS_PATH_REGEX.search(string)
            if match and len(match.group()) > min_length:
                rules += ['WINDOWS_PATH_REGEX']
            match = regex.MAC_REGEX.search(string)
            if match and len(match.group()) > min_length:
                rules += ['MAC_REGEX']
            match = regex.DATE1_REGEX.search(string)
            if match and len(match.group()) > min_length:
                rules += ['DATE1_REGEX']
            match = regex.DATE2_REGEX.search(string)
            if match and len(match.group()) > min_length:
                rules += ['DATE2_REGEX']
            match = regex.DATE3_REGEX.search(string)
            if match and len(match.group()) > min_length:
                rules += ['DATE3_REGEX']

            match = regex.UNIX_PATH_REGEX.search(string)
            if match:
                valid_path = False
                match_str = match.group()
                if len(match_str) <= min_length:
                    continue
                if ((match_str.startswith("'") and match_str.endswith("'")) or (match_str.startswith('"') and match_str.endswith('"'))):
                    valid_path = True
                elif any(char in SPECIAL_CHARS for char in match_str):
                    valid_path = True
                    for i in SPECIAL_CHARS:
                        if i in match_str:
                            index = match_str.index(i)
                            if index > 0 and match_str[index - 1] != "\\":
                                valid_path = False
                else:
                    valid_path = True
                if valid_path:
                    rules += ['UNIX_PATH_REGEX']

            if rules:
                output += ['{} ({})'.format(string, ', '.join(rules))]
        return output

    @staticmethod
    def interesting_plaintext(json):
        return '\n'.join(json)
