# Autoname

Autoname is a tool that renames based on the EXIF `DateTimeOriginal` of the photos and videos. If there is no EXIF in the media files, it will use the earliest creation or modification time of the file for renaming.

`python 3.11`

## Getting Started

### As User

Download the latest release [here](https://github.com/gymgle/autoname/releases)

#### Usage

```shell
usage: autoname [-h] [-d DIR] [-f FORMAT] [-r] [-oi] [-ov] [-p] [-v]

options:
  -h, --help            show this help message and exit
  -d DIR, --dir DIR     path to directory needed rename
  -f FORMAT, --format FORMAT
                        new name format in python datetime
  -r, --recursion       recursion rename all files in directory
  -oi, --only-image     rename only for image type
  -ov, --only-video     rename only for video type
  -p, --preview         preview new filename without rename
  -v, --version         show version
```

### As Developer

```shell
# 1. Clone this project.
$ git clone https://github.com/gymgle/autoname.git

# 2. Install pip requirements. 
$ cd autoname
$ pip3 install -r requirements.txt

# 3. Try it!
$ python autoname.py
```

### How to Build?

Build Windows/Linux/macOS executable binary file via PyInstaller.

1. Install PyInstaller
    ``` shell
    $ pip install pyinstaller
    ```

2. Prepare UPX (Optional)

    Download UPX [Here](https://github.com/upx/upx/releases), put `upx.exe` (Windows) to project root directory or your Python Virtual Env dir, eg. `venv\Scripts` for Windows.

3. Package project
    ```shell
    $ pyinstaller -F -i ./assets/icon.ico autoname.py
    ```

You can find the packaged `autoname` in `dist` dir.
