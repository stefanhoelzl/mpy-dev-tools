import tempfile
import time
import shutil
import sys

from mpy_fuse import MpyFuse
from mpy_sync import sync
from mpy_device import MpyDevice


def exec_file(device, script, output=None):
    with MpyDevice(device) as dev:
        dev.execfile(script, output=output)


def run(device, script, syncpath, script_output=None):
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
    yield "Run script"
    exec_file(device, script, output=script_output)


if __name__ == '__main__':
    from cli import mpy_run_parser
    args = mpy_run_parser.parse_args()

    for s in run(args.device, args.script, args.sync_path,
                 script_output=sys.stdout):
        print(s)