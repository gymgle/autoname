#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import os.path
import platform
from datetime import datetime, timezone
from sys import exit

import exifread
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

# Define version
Version = '0.1.1'

# File Extension Definition
Photos = ['.jpg', '.jpeg', '.heic', '.png', '.gif']
Videos = ['.mp4', '.mov']


def auto_rename(file_path: str) -> bool:
    """
    Auto rename
    :param file_path: str, path to directory
    :return: bool: success
    """
    for filename in os.listdir(file_path):
        abs_filename = os.path.join(file_path, filename)
        if os.path.isfile(abs_filename):
            file_ext = os.path.splitext(filename)[-1].lower()
            if file_ext in Photos:
                if only_video:
                    continue
                rename_photo(abs_filename)
            elif file_ext in Videos:
                if only_image:
                    continue
                rename_media(abs_filename)
            else:
                print('unsupported file format:', filename)
        elif os.path.isdir(abs_filename):
            print('directory:', abs_filename)
            if recursion:
                auto_rename(abs_filename)
        else:
            print('unknown file:', filename)
    return True


def rename_photo(filepath: str) -> bool:
    """
    Rename photo with EXIF
    :param filepath: str, path to photo
    :return:
    """
    with open(filepath, 'rb') as f:
        try:
            tags = exifread.process_file(f)
        except Exception as e:
            print(f'get exif tags from %s error: %s' % (filepath, e))
            tags = dict()

    if 'EXIF DateTimeOriginal' in tags:
        exif_date = str(tags['EXIF DateTimeOriginal'])
        rename_with_datetime(filepath, datetime.strptime(exif_date, '%Y:%m:%d %H:%M:%S'))
    else:
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
    try:
        ts = datetime.strptime(exif_date, '%Y-%m-%d %H:%M:%S').timestamp()
    except OSError:
        ts = 0.0
    if ts > 0:
        utc_time = datetime.strptime(exif_date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        local_time = utc_time.astimezone(datetime.now().astimezone().tzinfo)
    else:  # no metadata found, use the min timestamp in birthtime / ctime / mtime
        file_stat = os.stat(filepath)
        dt_list = []
        for i in [int(file_stat.st_ctime), int(file_stat.st_mtime)]:
            if i > 0:
                dt_list.append(i)
        if platform.system().lower() == 'darwin':  # birthtime in macOS
            dt_list.append(int(file_stat.st_birthtime))
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
        print('skip:', os.path.basename(filepath))
        return True
    if preview:
        print(os.path.basename(filepath), '->', os.path.basename(new_path))
        return True

    # Dangerous Ops: Rename
    # Change name if the new path exist: add the timestamp after the date taken
    if os.path.exists(new_path):
        print('same filename exist:', os.path.basename(filepath), '->', os.path.basename(new_path))
        ts = datetime.now().timestamp() * 1000
        new_name = '{date}-{timestamp}{ext}'.format(date=date_taken, timestamp=str(int(ts)),
                                                    ext=os.path.splitext(filepath)[-1].lower())
        new_path = os.path.join(os.path.dirname(filepath), new_name)
    os.rename(filepath, new_path)
    print('success:', os.path.basename(filepath), '->', os.path.basename(new_path))

    return True


def test_func() -> (bool, str):
    """
    Test input is valid or not before processing
    :return: (bool, str), bool: valid or not, str: error msg
    """
    # Check file path
    if not dir_path:
        return False, 'file path need to be specified with -p argument'

    if not os.path.exists(dir_path):
        return False, f'{dir_path} is not exist'

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
    parser.add_argument('-r', '--recursion', action='store_true', default=False,
                        help='recursion rename all files in directory')
    parser.add_argument('-oi', '--only-image', action='store_true', default=False,
                        help='rename only for image type')
    parser.add_argument('-ov', '--only-video', action='store_true', default=False,
                        help='rename only for video type')
    parser.add_argument('-pv', '--preview', action='store_true', default=False,
                        help='preview new filename without rename')
    parser.add_argument('-v', '--version', action='store_true', help='show version', default=False)
    args = vars(parser.parse_args())
    dir_path = args.get('path', '')
    date_format = args.get('format', '')
    file_datetime = args.get('datetime', '')
    recursion = args.get('recursion', False)
    only_image = args.get('only_image', False)
    only_video = args.get('only_video', False)
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
    auto_rename(dir_path)
