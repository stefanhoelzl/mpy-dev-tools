import os
import shutil
from pathlib import Path

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

def sync(src, dest):
    last_sync = src / Path('.last_sync')
    if last_sync.is_file():
        last_sync_time = os.stat(str(last_sync)).st_mtime
    else:
        last_sync_time = 0

    src = Path(src)
    dest = Path(dest)
    for f in src.glob('**/*'):
        mtime = os.stat(str(f)).st_mtime
        if mtime > last_sync_time:
            relative = f.relative_to(src)
            f_dest = dest / relative

            if f.is_dir() and not f.exists():
                f_dest.mkdir(parents=True, exist_ok=True)
                yield DirectoryCreated(relative)
            else:
                shutil.copy(str(f), str(f_dest))
                yield FileUpdated(relative)

    last_sync.touch(exist_ok=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("src", help="Local source code directory")
    parser.add_argument("dest", help="Micropython device mountpoint")
    args = parser.parse_args()
    for p in sync(args.src, args.dest):
        print(str(p))