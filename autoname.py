#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import os.path
import platform
import re
from datetime import datetime, timezone
from multiprocessing import freeze_support
from sys import exit, stdout

import exifread
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from loguru import logger

# Define version
Version = '0.3.0'

# File Extension Definition
Photos = ['.jpg', '.jpeg', '.heic', '.png', '.gif', '.nef']
Videos = ['.mp4', '.mov']

LOGGER_FORMAT = "<green>{time: YYYY-MM-DD HH:mm:ss}</green> ｜ <level>{message}</level>"


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
                logger.warning(f'skip unsupported file: {filename}')
        elif os.path.isdir(abs_filename):
            if recursion:
                logger.info(f'directory: {abs_filename}')
                auto_rename(abs_filename)
        else:
            logger.warning(f'unknown file: {filename}')
    return True


def rename_photo(filepath: str) -> bool:
    """
    Rename photo with EXIF
    :param filepath: str, path to photo
    :return:
    """
    if rename_with_datetime_from_filename(filepath):
        return True

    with open(filepath, 'rb') as f:
        try:
            tags = exifread.process_file(f)
        except Exception as e:
            logger.error(f'get exif tags from %s error: %s' % (filepath, e))
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
    if rename_with_datetime_from_filename(filepath):
        return True

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


def rename_with_datetime_from_filename(filepath: str) -> bool:
    """
    Rename with the datetime from filename
    :param filepath: str, path to file
    :return: bool, True: rename success, False: no timestamp found in filename
    """
    # If filename already has format as given by date_format, skip
    _, filename = os.path.split(filepath)
    name, _ = os.path.splitext(filename)
    if is_given_format(name):
        logger.info(f'skip: {filename}')
        return True

    # If regex option is enabled and the timestamp in filename is valid, rename it with the timestamp
    if regex:
        dt = datetime_from_filename(filename)
        if dt:  # If timestamp is valid
            rename_with_datetime(filepath, dt)
            return True
    return False


def rename_with_datetime(filepath: str, exif_date: datetime) -> bool:
    """
    Rename the file with given datetime
    :param filepath: path to file
    :param exif_date: datetime object
    :return: bool: True/False
    """
    date_taken = exif_date.strftime(date_format)
    new_name = date_taken + os.path.splitext(filepath)[-1]
    new_path = os.path.join(os.path.dirname(filepath), new_name)
    if filepath == new_path:  # Skip already in demanded name
        logger.warning(f'skip: {os.path.basename(filepath)}')
        return True
    if os.path.basename(filepath).startswith(date_taken):  # Skip if a valid timestamp already in demanded name
        logger.warning(f'skip: {os.path.basename(filepath)}')
        return True
    if preview:
        logger.info(f'{os.path.basename(filepath)} -> {os.path.basename(new_path)}')
        return True

    # Dangerous Ops: Rename
    # Change name if the new path exist: add original filename after the date taken
    if os.path.exists(new_path):
        original_filename = os.path.basename(filepath)
        new_name = '{date}_{org_filename}'.format(date=date_taken, org_filename=original_filename)
        new_path = os.path.join(os.path.dirname(filepath), new_name)
    os.rename(filepath, new_path)
    logger.success(f'{os.path.basename(filepath)} -> {os.path.basename(new_path)}')

    return True


def datetime_from_filename(filename) -> datetime | None:
    """
    Extract datetime from filename
    :param filename: str
    :return: datetime object
    """
    # Photo names for Android: IMG_20240316_101520.jpg
    # Video names for Android: VID_20240316_101520.mp4
    # Exceptions: xxx_123456_20240316101520123.jpg
    pattern = r'([12]\d{3})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])_?([01]\d|2[0-3])([0-5]\d)([0-5]\d)'
    match = re.search(pattern, filename)

    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))
        second = int(match.group(6))

        try:
            dt = datetime(year, month, day, hour, minute, second)
            return dt
        except ValueError:
            return None
    else:
        return None


def is_given_format(filename_without_ext: str) -> bool:
    """
    Check if the filename has format as given by date_format
    :param filename_without_ext: str
    :return: bool
    """
    try:
        datetime.strptime(filename_without_ext, date_format)
        return True
    except ValueError:
        return False


def test_func() -> (bool, str):
    """
    Test input is valid or not before processing
    :return: (bool, str), bool: valid or not, str: error msg
    """
    # Check file path
    if not dir_path:
        return False, 'file path need to be specified with -d argument'

    if not os.path.exists(dir_path):
        return False, f'{dir_path} is not exist'

    # Check date format
    try:
        datetime.now().strftime(date_format)
    except ValueError as e:
        return False, f'date format invalid: {date_format}, {e}'

    return True, 'tests passed'


def init_logger(level: str = 'INFO') -> None:
    """
    Init logger
    :return: None
    """
    logger.remove()
    logger.add(stdout, colorize=True, format=LOGGER_FORMAT, level=level)
    logger.add('rename_{time}.log', format=LOGGER_FORMAT, level=level,
               rotation='10MB', encoding='utf-8', enqueue=True, compression='zip')


def print_version():
    """
    Print version info
    :return: None
    """
    print(f'version {Version}')


if __name__ == '__main__':
    freeze_support()
    # Args analysis
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir', type=str, default='',
                        help='path to directory needed rename')
    parser.add_argument('-f', '--format', type=str, default='%Y-%m-%d %H.%M.%S',
                        help='new name format in python datetime')
    parser.add_argument('-r', '--recursion', action='store_true', default=False,
                        help='recursion rename all files in directory')
    parser.add_argument('-re', '--regex', action='store_true', default=True,
                        help='extract timestamps from file name using regular expressions')
    parser.add_argument('-oi', '--only-image', action='store_true', default=False,
                        help='rename only for image type')
    parser.add_argument('-ov', '--only-video', action='store_true', default=False,
                        help='rename only for video type')
    parser.add_argument('-p', '--preview', action='store_true', default=False,
                        help='preview new filenames without renaming')
    parser.add_argument('-ll', '--loglevel', type=str, default='INFO',
                        choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
                        help='set log level, default: INFO, others: DEBUG, WARNING, ERROR, CRITICAL')
    parser.add_argument('-v', '--version', action='store_true', help='show version', default=False)
    args = vars(parser.parse_args())
    dir_path = args.get('dir', '')
    date_format = args.get('format', '')
    file_datetime = args.get('datetime', '')
    recursion = args.get('recursion', False)
    regex = args.get('regex', True)
    only_image = args.get('only_image', False)
    only_video = args.get('only_video', False)
    preview = args.get('preview', False)
    logger_level = args.get('loglevel', 'INFO')
    version = args.get('version', False)

    init_logger(logger_level)

    # Show version
    if version:
        print_version()
        exit(0)

    # Test input is valid or not before processing
    ok, err = test_func()
    if not ok:
        logger.error(err)
        exit(0)

    # Get started
    auto_rename(dir_path)
