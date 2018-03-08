# pylint: disable=missing-docstring
# pylint: disable=no-self-use
# pylint: disable=unused-argument

import shutil
import subprocess

from snake import error
from snake import scale
from snake.scales.strings import regex


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
        return {'strings': str(subprocess.check_output(["strings", file.file_path]), encoding="utf-8").split('\n')}

    @staticmethod
    def all_strings_plaintext(json):
        return '\n'.join(json['strings'])

    @scale.command({
        'info': 'This function will return interesting strings found within the file'
    })
    def interesting(self, args, file, opts):
        strings = str(subprocess.check_output(["strings", file.file_path]), encoding="utf-8").split('\n')
        # TODO: Review the regexes associated with interesting strings
        output = ''
        for string in strings:
            if regex.IPV4_REGEX.search(string):
                output += [string + ' (IPV4_REGEX)']
            if regex.IPV6_REGEX.search(string):
                output += [string + ' (IPV6_REGEX)']
            if regex.EMAIL_REGEX.search(string):
                output += [string + ' (EMAIL_REGEX)']
            if regex.URL_REGEX.search(string):
                output += [string + ' (URL_REGEX)']
            if regex.DOMAIN_REGEX.search(string):
                output += [string + ' (DOMAIN_REGEX)']
            if regex.WINDOWS_PATH_REGEX.search(string):
                output += [string + ' (WINDOWS_PATH_REGEX)']
            if regex.UNIX_PATH_REGEX.search(string):
                output += [string + ' (UNIX_PATH_REGEX)']
            if regex.MAC_REGEX.search(string):
                output += [string + ' (MAC_REGEX)']
            if regex.DATE1_REGEX.search(string):
                output += [string + ' (DATE1_REGEX)']
            if regex.DATE2_REGEX.search(string):
                output += [string + ' (DATE2_REGEX)']
            if regex.DATE3_REGEX.search(string):
                output += [string + ' (DATE3_REGEX)']
        return {'hits': output}

    @staticmethod
    def interesting_plaintext(json):
        return '\n'.join(json['hits'])
