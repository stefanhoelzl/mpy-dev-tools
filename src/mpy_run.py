import tempfile
import shutil
from pathlib import Path

from ampy.files import Files
from ampy.pyboard import Pyboard

from mpy_fuse import MpyFuse
from mpy_sync import sync


def exec_file(device, script):
    yield 'Run {}'.format(script)
    pyb = Pyboard(device)
    pyb.enter_raw_repl()
    with open(script, 'rb') as f:
        for line in f.readlines():
            ret = pyb.exec(line)
            if len(ret) > 0:
                yield str(ret)[2:-5]
    pyb.exit_raw_repl()
    pyb.close()


def run(script, device, syncpath=None):
    if not syncpath:
        syncpath = Path(script).parent

    mntpoint = tempfile.mkdtemp()

    fuse = MpyFuse(device, mntpoint)
    fuse.mount()
    yield 'Device {} mounted at {}'.format(device, mntpoint)
    yield 'Synchronize'
    for f in sync(syncpath, mntpoint): yield f
    fuse.unmount()
    yield 'Device unmounted'

    shutil.rmtree(mntpoint)

    yield from exec_file(device, script)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("script", help=".py-Script to run")
    parser.add_argument("device", help="Micropython Device")
    args = parser.parse_args()

    for s in run(args.script, args.device): print(s)