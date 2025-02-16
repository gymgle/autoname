#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import os.path
import platform
import re
from datetime import datetime, timezone, timedelta
from multiprocessing import freeze_support
from sys import exit, stdout

import exifread
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from loguru import logger

# Define version
Version = '0.4.0'

# File Extension Definition
Photos = ['.jpg', '.jpeg', '.heic', '.png', '.gif', '.nef']
Videos = ['.mp4', '.mov']

LOGGER_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> ｜ <level>{message}</level>"


def auto_rename(file_path: str) -> bool:
    """
    Auto rename
    :param file_path: str, path to directory
    :return: bool: success
    """
    # User specified extensions
    specified_ext_list = []
    if extensions:  # If specified extensions option is enabled, add dot to user specified extensions
        specified_ext_list = [f'.{ext}' for ext in extensions.lower().split(',')]

    # Traverse and rename files
    for filename in os.listdir(file_path):
        abs_filename = os.path.join(file_path, filename)
        # Handling file photo and video files
        if os.path.isfile(abs_filename):
            file_ext = os.path.splitext(filename)[-1].lower()
            # If specified extensions option is enabled, only rename files with specified extensions
            if specified_ext_list and file_ext not in specified_ext_list:
                continue

            if file_ext in Photos:
                if only_video:
                    continue
                rename_photo(abs_filename)
            elif file_ext in Videos:
                if only_image:
                    continue
                rename_video(abs_filename)
            else:
                logger.warning(f'skip unsupported file: {filename}')
        # Handling directories
        elif os.path.isdir(abs_filename):
            if recursion:
                logger.info(f'directory: {abs_filename}')
                auto_rename(abs_filename)
        else:
            logger.warning(f'unknown file: {filename}')
    return True


def rename_photo(filepath: str) -> bool:
    """
    Rename photo file according to priority
    :param filepath: str, path to photo
    :return: bool, True: rename success, False: no timestamp found
    """
    # Priority 1. Rename with datetime from filename
    if rename_with_datetime_from_filename(filepath):
        return True

    # Priority 2. Rename with EXIF Info
    with open(filepath, 'rb') as f:
        try:
            tags = exifread.process_file(f)
        except Exception as e:
            logger.error(f'get exif tags from %s error: %s' % (filepath, e))
            tags = dict()

    if 'EXIF DateTimeOriginal' in tags:
        exif_date = str(tags['EXIF DateTimeOriginal'])
        rename_with_datetime(filepath, datetime.strptime(exif_date, '%Y:%m:%d %H:%M:%S'))

    # Priority 3. Rename with metadata or file attributes
    else:
        return rename_media(filepath)
    return True


def rename_video(filepath: str) -> bool:
    """
    Rename video file according to priority
    :param filepath: str, path to video
    :return: bool, True: rename success, False: no timestamp found
    """
    # Priority 1. Rename with datetime from filename
    if rename_with_datetime_from_filename(filepath):
        return True

    # Priority 2. Rename with metadata or file attributes
    return rename_media(filepath)


def rename_media(filepath: str) -> bool:
    """
    Rename media file with metadata or file attributes
    :param filepath: str, path to media file
    :return: bool, True: rename success, False: no timestamp found
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
    else:  # no metadata found, use the min timestamp in birthtime / ctime / mtime / filename timestamp
        file_stat = os.stat(filepath)
        dt_list = []
        for i in [int(file_stat.st_ctime), int(file_stat.st_mtime)]:
            if i > 0:
                dt_list.append(i)
        if platform.system().lower() == 'darwin':  # birthtime in macOS
            dt_list.append(int(file_stat.st_birthtime))

        # Try to get timestamp from filename
        _, filename = os.path.split(filepath)
        dt_from_filename = datetime_from_filename(filename)
        if dt_from_filename:
            dt_list.append(int(dt_from_filename.timestamp()))

        ctime = min(dt_list)
        local_time = datetime.fromtimestamp(ctime)
    return rename_with_datetime(filepath, local_time)


def rename_with_datetime_from_filename(filepath: str) -> bool:
    """
    Rename with the datetime from filename
    :param filepath: str, path to file
    :return: bool, True: rename success, False: no timestamp found in filename
    """
    _, filename = os.path.split(filepath)

    # If force_rename option not enabled, SKIP if the filename is already in the desired format
    if not force_rename:
        name, _ = os.path.splitext(filename)
        if is_given_format(name):
            logger.info(f'skip: {filename}')
            return True

    # If disable_regex option is not enabled, try to rename it with the timestamp in filename
    if not disable_regex:
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
    # Photo name for Android: IMG_20240316_101520.jpg
    # Video name for Android: VID_20240316_101520.mp4
    # Files name for OneDrive Backup: 20240316_101520666_iOS.heic
    # Exception: xxx_123456_20240316101520123.jpg
    pattern = r'([12]\d{3})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])[_\-\s]?([01]\d|2[0-3])([0-5]\d)([0-5]\d)(\d{3})?'
    match = re.search(pattern, filename)

    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))
        second = int(match.group(6))
        microsecond = int(match.group(7)) if match.group(7) else 0

        try:
            dt = datetime(year, month, day, hour, minute, second, microsecond)
            if regex_offset:
                dt = dt + timedelta(hours=regex_offset)
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

    # Check log path
    if log_path:
        if not os.path.exists(log_path):
            return False, f'log path {log_path} is not exist'

    # Check date format
    try:
        datetime.now().strftime(date_format)
    except ValueError as e:
        return False, f'date format invalid: {date_format}, {e}'

    # Check specified extensions
    if extensions:
        for ext in extensions.lower().split(','):
            ext_with_dot = f'.{ext}'
            if ext_with_dot not in Photos + Videos:
                return False, f'extension {ext} is not supported'

    return True, 'tests passed'


def init_logger(level: str = 'INFO') -> None:
    """
    Init logger
    :return: None
    """
    logger.remove()
    # Output to console
    logger.add(stdout, colorize=True, format=LOGGER_FORMAT, level=level)
    # Output to log file
    log_file = os.path.join(log_path, 'autoname_{time}.log') if log_path else 'autoname_{time}.log'
    logger.add(log_file, format=LOGGER_FORMAT, level=level, rotation='10MB', encoding='utf-8',
               enqueue=True, compression='zip')


def print_version():
    """
    Print version info
    :return: None
    """
    print(f'version {Version}')


if __name__ == '__main__':
    # Fix multiprocessing issue in Windows with PyInstaller
    freeze_support()

    # Args analysis
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir', type=str, default='',
                        help='path to the directory that needs renaming')
    parser.add_argument('-f', '--format', type=str, default='%Y-%m-%d %H.%M.%S',
                        help='new name format in python datetime')
    parser.add_argument('-r', '--recursion', action='store_true', default=False,
                        help='recursively rename all files in the subdirectories, disabled by default')
    parser.add_argument('-p', '--preview', action='store_true', default=False,
                        help='preview new filenames without actually renaming them')
    parser.add_argument('-dr', '--disable_regex', action='store_true', default=False,
                        help='timestamp is extracted from the filename by default. Enable this option to skip filename regex extraction')
    parser.add_argument('-ext', '--extension', type=str, default='',
                        help='only rename files in specified extensions, separate extensions with a comma, e.g. "jpg,png,mov"')
    parser.add_argument('-fr', '--force_rename', action='store_true', default=False,
                        help='force rename even if the filename is already in the desired format, disabled by default')
    parser.add_argument('-ll', '--loglevel', type=str, default='INFO',
                        choices=('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
                        help='set log level, default: INFO, options: DEBUG, WARNING, ERROR, CRITICAL')
    parser.add_argument('-lp', '--log_path', type=str, default='',
                        help='log file path, default: current directory')
    parser.add_argument('-ro', '--regex_offset', type=float, default=0,
                        help='offset in hours when using regex from filename, e.g. 8 for UTC+8 if filename timezone is UTC')
    parser.add_argument('-oi', '--only-image', action='store_true', default=False,
                        help='rename only for image files, disabled by default')
    parser.add_argument('-ov', '--only-video', action='store_true', default=False,
                        help='rename only for video files, disabled by default')
    parser.add_argument('-v', '--version', action='store_true', default=False,
                        help='show version')

    args = vars(parser.parse_args())
    dir_path = args.get('dir', '')
    date_format = args.get('format', '')
    recursion = args.get('recursion', False)
    preview = args.get('preview', False)
    disable_regex = args.get('disable_regex', False)
    extensions = args.get('extension', '')
    force_rename = args.get('force_rename', False)
    log_level = args.get('loglevel', 'INFO')
    log_path = args.get('log_path', '')
    regex_offset = args.get('regex_offset', 0)
    only_image = args.get('only_image', False)
    only_video = args.get('only_video', False)
    version = args.get('version', False)

    init_logger(log_level)

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
