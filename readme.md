# Autoname

Autoname is a tool that renames files based on the EXIF `DateTimeOriginal` metadata of photos and videos. If the media files do not contain EXIF data, it will use the earliest creation or modification time of the file for renaming.

If the filename contains a usable timestamp, it will take priority over other methods and be used for renaming.

`python 3.11+`

## Getting Started

### As Users

Download the latest release [here](https://github.com/gymgle/autoname/releases)

#### Usage

```shell
usage: autoname [-h] [-d DIR] [-f FORMAT] [-r] [-p] [-dr] [-ext EXTENSION] [-fr] [-ll {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-lp LOG_PATH] [-ro REGEX_OFFSET] [-oi] [-ov] [-v]

options:
  -h, --help            show this help message and exit
  -d, --dir DIR         path to the directory that needs renaming
  -f, --format FORMAT   new name format in python datetime
  -r, --recursion       recursively rename all files in the subdirectories
  -p, --preview         preview new filenames without actually renaming them
  -dr, --disable_regex  timestamp is extracted from the filename by default. Enable this option to skip filename regex extraction
  -ext, --extension EXTENSION
                        only rename files in specified extensions, separate extensions with a comma, e.g. "jpg,png,mov"
  -fr, --force_rename   force rename even if the filename is already in the desired format
  -ll, --loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        set log level, default: INFO, options: DEBUG, WARNING, ERROR, CRITICAL
  -lp, --log_path LOG_PATH
                        log file path, default: current directory
  -ro, --regex_offset REGEX_OFFSET
                        offset in hours when using regex from filename, e.g. 8 for UTC+8 if filename timezone is UTC
  -oi, --only-image     rename only for image files
  -ov, --only-video     rename only for video files
  -v, --version         show version
```
#### How it works?

![Flowchat](./assets/flowchart.drawio.svg)

#### Examples

1. Preview new filenames for photos and videos in directory `D:\Photos\2025`.
   ```shell
   autoname -d D:\Photos\2025 -p
   ```

2. Rename photos and videos with the timezone offset of 8 hours when using regex from filename.
   ```shell
   autoname -ro 8 -d D:\Photos\2025
   autoname --regex_offset 8 -d D:\Photos\2025
   ```

3. Disable regex from filename, this will use EXIF data for first priority.
   ```shell
   autoname -dr -d D:\Photos\2025
   autoname --disable_regex -d D:\Photos\2025
   ```

4. Force to rename even if the filename is already in the desired format.
   ```shell
   autoname -fr -d D:\Photos\2025
   autoname --force_rename -d D:\Photos\2025
   ```

5. Force to rename and disable regex from filename. If the filename is already in the desired format, but the datetime is not correct, use this option combination to correct it.
   ```shell
   autoname -fr -dr -d D:\Photos\2025
   autoname --force_rename --disable_regex -d D:\Photos\2025
   ```

6. Rename only Photo files.
   ```shell
   autoname -oi -d D:\Photos\2025
   autoname --only-image -d D:\Photos\2025
   ```

7. Rename only specific extensions.
   ```shell
   autoname -ext heic,mov -d D:\Photos\2025
   autoname --extension heic,mov -d D:\Photos\2025
   ```

8. Recursively rename files in all the subdirectories.
   ```shell
   autoname -r -d D:\Photos
   autoname --recursion -d D:\Photos
   ```

### As Developers

```shell
# 1. Clone the repository.
$ git clone https://github.com/gymgle/autoname.git

# 2. Install pip requirements. 
$ cd autoname
$ pip3 install -r requirements.txt

# 3. Try it!
$ python autoname.py
```

Please **DO NOT** use `exifread 3.0.0` due to `exifread.heic.NoParser: hdlr` issue.
Details: https://github.com/ianare/exif-py/issues/184

### How to Build?

Build Windows/Linux/macOS executable binary file via PyInstaller.

1. Install PyInstaller
    ``` shell
    $ pip install pyinstaller
    ```

2. Prepare UPX (Optional)

    Download UPX [Here](https://github.com/upx/upx/releases), put `upx.exe` (Windows) to project root directory or your Python Virtual Env dir, e.g. `venv\Scripts` for Windows.

3. Build python script to executable binary file
    ```shell
    $ pyinstaller -F -i ./assets/icon.ico autoname.py
    ```

You can find the packaged `autoname` in `dist` dir.
