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
import os
from os import path
import shutil
import subprocess
import sys

import pkg_resources

from snake.config import constants
from snake.core import scale_manager as sm

# pylint: disable=missing-docstring


DEFAULT_REPO = "git+https://github.com/countercept/snake-scales#subdirectory="


def check(scale):
    print("Checking: {}".format(scale))
    scale_manager = sm.ScaleManager([])
    scale_manager._ScaleManager__load_scales([scale])  # pylint: disable=no-member, protected-access
    if scale not in scale_manager.scales:
        print("Scale not loadable: {}".format(scale))
    else:
        print("Scale loadable: {}".format(scale))


def install(scales, upgrade=False):
    # Check for pip3
    pip3 = shutil.which('pip3')
    if not pip3:
        print("Could not find 'pip3'!")
        sys.exit(1)

    # Pre process
    scales_ = []
    for scale in scales:
        # TODO: Make robust cater for all scenarios
        if len(scale.rsplit('=', 1)) > 1:  # XXX: Handle subdirectory, don't assume it is last arg!
            r, s = scale.rsplit('=', 1)  # pylint: disable=invalid-name
            scales_ += [("{}=".format(r), s)]
        elif len(scale.rsplit('/', 1)) > 1:
            r, s = scale.rsplit('/', 1)  # pylint: disable=invalid-name
            scales_ += [("{}/".format(r), s)]
        else:
            scales_ += [(DEFAULT_REPO, scale)]

    # Install scales
    for repo, scale in scales_:  # pylint: disable=invalid-name
        print("Installing: {}".format(scale))
        if upgrade:
            proc = subprocess.run([pip3, 'install', '--upgrade', '{}{}'.format(repo, scale)])
        else:
            proc = subprocess.run([pip3, 'install', '{}{}'.format(repo, scale)])
        if proc.returncode:
            print("Failed to install: {}".format(scale))
            sys.exit(1)

        # Copy config if present
        scale_path = imp.find_module('snake_{}'.format(scale))[1]
        if path.exists(path.join(scale_path, '{}.conf'.format(scale))):
            scales_dir = path.join(constants.ETC_DIR, 'scales')
            if not path.exists(scales_dir):
                os.makedirs(scales_dir, exist_ok=True)
            shutil.copy(path.join(scale_path, '{}.conf'.format(scale)), path.join(scales_dir, '{}.conf.example'.format(scale)))
            if not path.exists(path.join(scales_dir, '{}.conf'.format(scale))):
                shutil.copy(path.join(scales_dir, '{}.conf.example'.format(scale)), path.join(scales_dir, '{}.conf'.format(scale)))

    # Reload pkg_resources
    imp.reload(pkg_resources)

    # Check installed scales
    for _repo, scale in scales_:
        check(scale)


def main():
    # NOTE: subparsers bug: https://bugs.python.org/issue9253#msg186387
    parser = argparse.ArgumentParser(prog='snake')
    subparsers = parser.add_subparsers(help='command help')
    subparsers.required = True
    subparsers.dest = 'command'
    parser_check = subparsers.add_parser('check', help='check the status of a scale')
    parser_check.add_argument('scale', nargs=1, help='a scale')
    parser_install = subparsers.add_parser('install', help='install a scale or multiple scales')
    parser_install.add_argument('scale', nargs='+', help='a scale or multiple scales')
    parser_upgrade = subparsers.add_parser('upgrade', help='upgrade a scale or multiple scales')
    parser_upgrade.add_argument('scale', nargs='+', help='a scale or multiple scales')
    args = parser.parse_args()

    if args.command == 'check':
        check(args.scale[0])  # XXX: Hmm, namespace clash? nargs is 1
        return
    if args.command == 'install':
        install(args.scale)
        return
    if args.command == 'upgrade':
        install(args.scale, upgrade=True)
        return


if __name__ == "__main__":
    main()
