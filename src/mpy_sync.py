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


def sync(src, dest, cleanup=True):
    last_sync = src / Path('.last_sync')
    if last_sync.is_file():
        last_sync_time = os.stat(str(last_sync)).st_mtime
    else:
        last_sync_time = 0

    src = Path(src)
    dest = Path(dest)
    for f_src in src.glob('**/*'):
        mtime = os.stat(str(f_src)).st_mtime
        if mtime > last_sync_time:
            relative = f_src.relative_to(src)
            f_dest = dest / relative

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

    for f_dest in dest.glob('**/*'):
        relative = f_dest.relative_to(dest)
        f_src = src / relative
        if f_dest.is_file() and not f_src.exists():
            f_dest.unlink()
            yield FileDeleted(relative)
        elif f_dest.is_dir() and not f_src.exists():
            shutil.rmtree(f_dest)
            yield DirectoryDeleted(relative)

    last_sync.touch(exist_ok=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("src", help="Local source code directory")
    parser.add_argument("dest", help="Micropython device mountpoint")
    args = parser.parse_args()
    for p in sync(args.src, args.dest):
        print(str(p))