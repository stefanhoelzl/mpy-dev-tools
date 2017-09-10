import sys
import time
from multiprocessing import Process

from ampy.pyboard import Pyboard
from ampy.files import Files

from mpy_sync import sync
from mpy_fuse import mount

DEVICE = '/dev/tty.SLAB_USBtoUART'
MNTPOINT = 'device'

fuse_process = Process(target=mount, args=(DEVICE, MNTPOINT, False))
fuse_process.daemon = True
fuse_process.start()
time.sleep(0.5)
if fuse_process.exitcode: raise Exception('Mounting failed')
print("Device {} mounted".format(DEVICE))

try:
    print("Syncronize")
    for p in sync('src', MNTPOINT): print(str(p))
finally:
    fuse_process.terminate()
    print('Device unmounted')

script = sys.argv[1]
print("Run script {}".format(script))
board = Pyboard('/dev/tty.SLAB_USBtoUART')
files = Files(board)

lines = str(files.run(script))[2:-1].split('\\r\\n')
for line in lines:
    print(line)
