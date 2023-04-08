#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import os.path
import exifread
from sys import exit
from datetime import datetime, timezone
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

# Define version
Version = '0.1.0'

# File Extension Definition
Photos = ['.jpg', '.jpeg', '.heic', '.png']
Videos = ['.mp4', '.mov']


def auto_rename() -> bool:
    """
    Auto rename
    :return: bool: success
    """
    for filename in os.listdir(file_path):
        file_ext = os.path.splitext(filename)[-1].lower()
        if file_ext in Photos:
            if only_video:
                continue
            rename_photo(os.path.join(file_path, filename))
        elif file_ext in Videos:
            if only_image:
                continue
            rename_media(os.path.join(file_path, filename))
        else:
            print('unsupported file format:', filename)
    return True


def rename_photo(filepath: str) -> bool:
    """
    Rename photo with EXIF
    :param filepath: str, path to photo
    :return:
    """
    with open(filepath, 'rb') as f:
        tags = exifread.process_file(f)

    if 'EXIF DateTimeOriginal' in tags:
        exif_date = str(tags['EXIF DateTimeOriginal'])
        rename_with_datetime(filepath, datetime.strptime(exif_date, '%Y:%m:%d %H:%M:%S'))
    else:
        print('no EXIF DateTimeOriginal tag found:', filepath)
        if ct_enabled:
            return rename_media(filepath)
    return True


def rename_media(filepath: str) -> bool:
    """
    Rename media with metadata
    :param filepath: str, path to video
    :return:
    """
    with createParser(filepath) as ps:
        metadata = extractMetadata(ps)
    exif_dict = metadata.exportDictionary()['Metadata']
    exif_date = str(exif_dict.get('Creation date', '1904-01-01 00:00:00'))  # maybe before 1970 (1904-01-01...)
    if datetime.strptime(exif_date, '%Y-%m-%d %H:%M:%S').timestamp() > 0:
        utc_time = datetime.strptime(exif_date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        local_time = utc_time.astimezone(datetime.now().astimezone().tzinfo)
    else:  # no metadata found, use the min timestamp in birthtime / ctime / mtime
        file_stat = os.stat(filepath)
        dt_list = []
        for i in [int(file_stat.st_birthtime), int(file_stat.st_ctime), int(file_stat.st_mtime)]:
            if i > 0:
                dt_list.append(i)
        ctime = min(dt_list)
        local_time = datetime.fromtimestamp(ctime)
    return rename_with_datetime(filepath, local_time)


def rename_with_datetime(filepath: str, exif_date: datetime) -> bool:
    """
    Rename the file with given datetime
    :param filepath: path to file
    :param exif_date: datetime object
    :return: bool: True/False
    """
    date_taken = exif_date.strftime(date_format)
    new_name = date_taken + os.path.splitext(filepath)[-1].lower()
    new_path = os.path.join(os.path.dirname(filepath), new_name)
    if filepath == new_path:  # Skip already in demanded name
        print('skip:', os.path.split(filepath)[-1])
        return True
    if preview:
        print(os.path.split(filepath)[-1], '->', os.path.split(new_path)[-1])
    else:
        # Dangerous Ops: Rename
        # Skip if new path exist
        if os.path.exists(new_path):
            print('same filename exist:', os.path.split(filepath)[-1], '->', os.path.split(new_path)[-1])
            return False
        os.rename(filepath, new_path)
        print('success:', os.path.split(filepath)[-1], '->', os.path.split(new_path)[-1])
    return True


def test_func() -> (bool, str):
    """
    Test input is valid or not before processing
    :return: (bool, str), bool: valid or not, str: error msg
    """
    # Check file path
    if not file_path:
        return False, 'file path need to be specified with -p argument'

    if not os.path.exists(file_path):
        return False, f'{file_path} is not exist'

    # Check date format
    try:
        datetime.now().strftime(date_format)
    except ValueError as e:
        return False, f'date format invalid: {date_format}, {e}'

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
    parser.add_argument('-f', '--format', type=str, default='%Y-%m-%d %H.%M.%S',
                        help='new name format in python datetime')
    parser.add_argument('-oi', '--only-image', action='store_true', default=False,
                        help='rename only for image type')
    parser.add_argument('-ov', '--only-video', action='store_true', default=False,
                        help='rename only for video type')
    parser.add_argument('-pv', '--preview', action='store_true', default=False,
                        help='preview new filename without rename')
    parser.add_argument('-ct', '--create-time', action='store_true', default=False,
                        help='use the media create time if no EXIF found')
    parser.add_argument('-v', '--version', action='store_true', help='show version', default=False)
    args = vars(parser.parse_args())
    file_path = args.get('path', '')
    date_format = args.get('format', '')
    file_datetime = args.get('datetime', '')
    only_image = args.get('only_image', False)
    only_video = args.get('only_video', False)
    ct_enabled = args.get('create_time', False)
    preview = args.get('preview', False)
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
