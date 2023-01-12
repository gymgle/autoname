#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
from sys import exit

# Define version
Version = '0.1.0'


def auto_rename() -> bool:
    return True


def test_func() -> (bool, str):
    """
    Test input is valid or not before processing
    :return: (bool, str), bool: valid or not, str: error msg
    """
    # TODO: TEST

    return True, 'tests passed'


def print_version():
    """
    Print version info
    :return: None
    """
    print(f'version {Version}')


if __name__ == '__main__':
    # Args analysis
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--auto', action='store_true', default=False,
                        help='auto rename files of given path')
    parser.add_argument('-p', '--path', type=str, default='',
                        help='path to files needed rename')
    parser.add_argument('-f', '--format', type=str, default='%Y-%m-%d %H:%M:%S',
                        help='new name format in python datetime')
    parser.add_argument('-t', '--datetime', type=str, default='original',
                        help='which datetime should be choosen for the new name: original, create, modify, filename')
    parser.add_argument('-d', '--android', action='store_true', default=False,
                        help='auto rename only for Android DCIM files')
    parser.add_argument('-w', '--wechat', action='store_true', default=False,
                        help='auto rename only for Wechat files')
    parser.add_argument('-v', '--version', action='store_true', help='show version', default=False)
    args = vars(parser.parse_args())
    auto = args.get('auto', False)
    file_path = args.get('path', '')
    file_format = args.get('format', '')
    file_datetime = args.get('datetime', '')
    android = args.get('android', False)
    wechat = args.get('wechat', False)
    version = args.get('version', False)

    # Show version
    if version:
        print_version()
        exit(0)

    # Test input is valid or not before processing
    ok, err = test_func()
    if not ok:
        print(err)
        exit(0)

    # Get started
    auto_rename()
