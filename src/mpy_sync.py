import os
import shutil
import re
import time
from pathlib import Path
import configparser


class SyncOperation(object):
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.path)

class FileCreated(SyncOperation): pass
class FileUpdated(SyncOperation): pass
class FileDeleted(SyncOperation): pass
class DirectoryCreated(SyncOperation): pass
class DirectoryDeleted(SyncOperation): pass
class Ignored(SyncOperation): pass


def read_ignore_patterns(config):
    ignored = []
    ignored_sync = []
    ignored_del = []
    if config.has_section('ignore'):
        ignored = list(config['ignore'])

    if config.has_section('ignore.sync'):
        ignored_sync = list(config['ignore.sync'])

    if config.has_section('ignore.delete'):
        ignored_del = list(config['ignore.delete'])
    return ignored+ignored_sync, ignored+ignored_del


def sync(src, dest, cleanup=True):
    """
    Generator which syncs a source-folder to a destination folder.
    Copies files where the modification date is newer then the last sync date.
    Last sync date is saved in .last_sync-file stored in the source-folder.
    Optional deletes files from destination folder if not existend in source folder.

    Can be configured with a ini-like .mpy_sync file in the source directory.

    :param src: source-folder
    :param dest: destination-folder
    :param cleanup: If true, files not existing in the source folder gets
     deleted form the destination folder (optional)
    :return: yields sync operations e.g. FileCreated, FileDeleted, FileUpdated,
     DirectoryCreated, DirectoryDeleted

.. code-block:: python

        for f in sync('myporject/src', '/mnt/mpy_fs', cleanup=True):
            print(f)

.. code-block:: ini

        [last_sync] # internals - do not modify this section
        123456.99

        [ignore] # File/Directory pattern to ignore over whole synchronisation process
        .gitignore
        # regular expression pattern accepted

        [ignore.sync] # File/Directory pattern ignored at copiing files to the board
        test

        [ignore.delete] # File/Directoy pattern ignored at deleting from the board
        boot.py
        main.py
    """
    sync_config_path = src / Path('.mpy_sync')
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(str(sync_config_path))

    if config.has_section('last_sync'):
        last_sync_time = float(list(config['last_sync'])[0])
    else:
        config.add_section('last_sync')
        last_sync_time = 0

    ignore_sync, ignore_delete = read_ignore_patterns(config)

    src = Path(src)
    dest = Path(dest)
    for f_src in src.glob('**/*'):
        mtime = os.stat(str(f_src)).st_mtime
        if mtime > last_sync_time:
            relative = f_src.relative_to(src)
            f_dest = dest / relative

            if any(re.match(pattern, str(relative))
                   for pattern in ignore_sync):
                yield Ignored(relative)
                continue

            if f_src.is_dir() and not f_dest.exists():
                f_dest.mkdir(parents=True, exist_ok=True)
                yield DirectoryCreated(relative)
            elif f_src.is_file():
                created = False
                if not f_dest.exists():
                    created = True
                shutil.copy(str(f_src), str(f_dest))
                if created:
                    yield FileCreated(relative)
                else:
                    yield FileUpdated(relative)

    if cleanup:
        for f_dest in dest.glob('**/*'):
            relative = f_dest.relative_to(dest)
            if any(re.match(pattern, str(relative))
                   for pattern in ignore_delete):
                yield Ignored(relative)
                continue

            f_src = src / relative
            if f_dest.is_file() and not f_src.exists():
                f_dest.unlink()
                yield FileDeleted(relative)
            elif f_dest.is_dir() and not f_src.exists():
                shutil.rmtree(str(f_dest))
                yield DirectoryDeleted(relative)

    config['last_sync'][str(time.time())] = None
    config.write(sync_config_path.open(mode='w'))


if __name__ == '__main__':
    from cli import mpy_sync_parser
    args = mpy_sync_parser.parse_args()
    for p in sync(args.src, args.dest):
        print(str(p))