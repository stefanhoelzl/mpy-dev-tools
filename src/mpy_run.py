import tempfile
import time
import shutil

from mpy_fuse import MpyFuse
from mpy_sync import sync
from mpy_device import MpyDevice


def exec_file(device, script):
    dev = MpyDevice(device)
    dev.execfile(script)


def run(device, script, syncpath=None):
    if syncpath:
        mntpoint = tempfile.mkdtemp()

        fuse = MpyFuse(device, mntpoint)
        fuse.mount()
        time.sleep(1)
        yield 'Device {} mounted at {}'.format(device, mntpoint)
        yield 'Synchronize'
        for f in sync(syncpath, mntpoint): yield f
        fuse.unmount()
        time.sleep(1)
        yield 'Device unmounted'

        shutil.rmtree(mntpoint)

    exec_file(device, script)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("device", help="Micropython Device")
    parser.add_argument("script", help=".py-Script to run")
    args = parser.parse_args()

    for s in run(args.device, args.script):
        print(s)