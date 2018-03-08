#!/usr/bin/python3
"""The snake command line utility.

This file exists to try and make the management of Snake easier. Currently its
only capability is to try and ease installation of Scales. But it will probably
do more at some point.

Examples:
    snake install SCALE_NAME
    snake install https://pypi.python.org/pypi/snake_SCALE_NAME
    snake install git+https://github.com/countercept/snake-scales/SCALE_NAME
    snake check SCALE_NAME
"""

import argparse
import imp
from os import path
import shutil
import subprocess
import sys

from snake.config import constants
from snake.core import scale_manager as sm

# pylint: disable=missing-docstring


DEFAULT_REPO = "git+https://github.com/countercept/snake-scales"


def check(scale):
    print("Checking: {}".format(scale))
    scale_manager = sm.ScaleManager([])
    scale_manager._ScaleManager__load_scales([scale])  # pylint: disable=no-member, protected-access
    if scale not in scale_manager.scales:
        print("Scale not loaded: {}".format(scale))
    else:
        print("Scale loaded: {}".format(scale))


def install(scales):
    # Check for pip3
    pip3 = shutil.which('pip3')
    if not pip3:
        print("Could not find 'pip3'!")
        sys.exit(1)

    # Pre process
    scales_ = []
    for scale in scales:
        if len(scale.rsplit('/', 1)) > 1:
            scales_ += [scale.rsplit('/', 1)]
        else:
            scales_ += [(DEFAULT_REPO, scale)]

    # Install scales
    for repo, scale in scales_:  # pylint: disable=invalid-name
        print("Installing: {}".format(scale))
        proc = subprocess.run([pip3, 'install', '{}/{}'.format(repo, scale)])
        if proc.returncode:
            print("Failed to install: {}".format(scale))

        # Copy config if present
        scale_path = imp.find_module('snake_{}'.format(scale))[1]
        if path.exists(path.join(scale_path, '{}.conf'.format(scale))):
            scales_dir = path.join(constants.ETC_DIR, 'scales')
            shutil.copy(path.join(scale_path, '{}.conf'.format(scale)), path.join(scales_dir, '{}.conf.example'.format(scale)))
            if not path.exists(path.join(scales_dir, '{}.conf'.format(scale))):
                shutil.copy(path.join(scales_dir, '{}.conf.example'.format(scale)), path.join(scales_dir, '{}.conf'.format(scale)))

    # Check installed scales
    for _repo, scale in scales:
        print("Checking: {}".format(scale))
        check(scale)


def main():
    # NOTE: subparsers bug: https://bugs.python.org/issue9253#msg186387
    parser = argparse.ArgumentParser(prog='snake')
    subparsers = parser.add_subparsers(help='command help')
    subparsers.required = True
    subparsers.dest = 'command'
    parser_install = subparsers.add_parser('check', help='check the status of a scale')
    parser_install.add_argument('scale', nargs=1, help='a scale')
    parser_install = subparsers.add_parser('install', help='install a scale or multiple scales')
    parser_install.add_argument('scale', nargs='+', help='a scale or multiple scales')
    args = parser.parse_args()

    if args.command == 'check':
        check(args.scale[0])  # XXX: Hmm, namespace clash? nargs is 1
        return
    if args.command == 'install':
        install(args.scale)
        return


if __name__ == "__main__":
    main()
