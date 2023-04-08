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
    parser.add_argument('-p', '--path', type=str, default='',
                        help='path to files needed rename')
    parser.add_argument('-f', '--format', type=str, default='%Y-%m-%d %H:%M:%S',
                        help='new name format in python datetime')
    parser.add_argument('-t', '--datetime', type=str, default='original',
                        help='which datetime should be choosen for the new name: original, create, modify, filename')
    parser.add_argument('-oi', '--only-image', action='store_true', default=False,
                        help='rename only for image type')
    parser.add_argument('-ov', '--only-video', action='store_true', default=False,
                        help='rename only for video type')
    parser.add_argument('-v', '--version', action='store_true', help='show version', default=False)
    args = vars(parser.parse_args())
    file_path = args.get('path', '')
    file_format = args.get('format', '')
    file_datetime = args.get('datetime', '')
    only_image = args.get('only-image', False)
    only_video = args.get('only-video', False)
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
