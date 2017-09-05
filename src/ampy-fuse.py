import sys
import errno

from ampy.pyboard import Pyboard

from fuse import FUSE, FuseOSError, Operations

class AmpyFuse(Operations):
    def __init__(self, device):
        self.board = Pyboard(device)
        self.board.enter_raw_repl()
        self.exec('import os')

    #
    # Ampy methods
    #

    def exec(self, command):
        self.board.exec(command)

    def eval(self, command):
        return self.board.eval(command).decode('utf-8')

    #
    # Filesystem methods
    #

    def access(self, path, mode):
        pass

    def chmod(self, path, mode):
        raise FuseOSError(0xF1)

    def chown(self, path, uid, gid):
        raise FuseOSError(0xF2)

    def getattr(self, path, fh=None):
        raise FuseOSError(0xF3)

    def readdir(self, path, fh):
        raise FuseOSError(0xF4)

    def readlink(self, path):
        raise FuseOSError(0xF5)

    def mknod(self, path, mode, dev):
        raise FuseOSError(0xF6)

    def rmdir(self, path):
        raise FuseOSError(0xF7)

    def mkdir(self, path, mode):
        raise FuseOSError(0xF8)

    def statfs(self, path):
        raise FuseOSError(0xF9)

    def unlink(self, path):
        raise FuseOSError(0xF0)

    def symlink(self, name, target):
        raise FuseOSError(0xFA)

    def rename(self, old, new):
        raise FuseOSError(0xFB)

    def link(self, target, name):
        raise FuseOSError(0xFC)

    def utimens(self, path, times=None):
        raise FuseOSError(0xFD)

    def destroy(self, path):
        self.board.exit_raw_repl()
        self.board.close()

    #
    # File methods
    #

    def open(self, path, flags):
        raise FuseOSError(errno.EPERM)

    def create(self, path, mode, fi=None):
        raise FuseOSError(errno.EPERM)

    def read(self, path, length, offset, fh):
        raise FuseOSError(errno.EPERM)

    def write(self, path, buf, offset, fh):
        raise FuseOSError(errno.EPERM)

    def truncate(self, path, length, fh=None):
        raise FuseOSError(errno.EPERM)

    def flush(self, path, fh):
        raise FuseOSError(errno.EPERM)

    def release(self, path, fh):
        raise FuseOSError(errno.EPERM)

    def fsync(self, path, fdatasync, fh):
        raise FuseOSError(errno.EPERM)


def main(device, mntpoint):
    FUSE(AmpyFuse(device), mntpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])