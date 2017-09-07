import sys
import errno
import os
import re

from ampy.pyboard import Pyboard, PyboardError

from fuse import FUSE, FuseOSError, Operations

class MpyFuse(Operations):
    def __init__(self, device):
        self.board = Pyboard(device)
        self.board.enter_raw_repl()
        self.exec('import os')
        self.file_handles = dict()

    #
    # Mpy methods
    #

    def exec(self, command):
        self.board.exec(command)

    def eval(self, var, command):
        try:
            ret = self.board.eval('{}.{}'.format(var, command)).decode('utf-8')
        except PyboardError as e:
            pattern = re.compile(r'OSError: \[Errno (?P<error_number>\d+)\]',
                                 re.MULTILINE)
            error_message = e.args[2].decode('utf-8')
            match = pattern.search(error_message)
            if match:
                error_number = int(match.group('error_number'))
                raise FuseOSError(error_number)
            else:
                raise
        else:
            return ret

    def create_var(self, var, command):
        self.board.exec("{} = {}".format(var, command))

    #
    # Filesystem methods
    #

    def access(self, path, mode):
        pass

    def chmod(self, path, mode):
        raise NotImplementedError()

    def chown(self, path, uid, gid):
        raise NotImplementedError()

    def getattr(self, path, fh=None):
        pattern = r'\((?P<st_mode>\d+), ' \
                  r'(?P<st_ino>\d+), ' \
                  r'(?P<st_dev>\d+), ' \
                  r'(?P<st_nlink>\d+), ' \
                  r'(?P<st_uid>\d+), ' \
                  r'(?P<st_gid>\d+), ' \
                  r'(?P<st_size>\d+), ' \
                  r'(?P<st_atime>\d+), ' \
                  r'(?P<st_mtime>\d+), ' \
                  r'(?P<st_ctime>\d+)\)'
        ret = self.eval("os", "stat('{}')".format(path))
        attrs = re.match(pattern, ret).groupdict()
        return {k: int(v) for k, v in attrs.items()}

    def readdir(self, path, fh):
        ret = self.eval("os", "listdir('{}')".format(path))
        return re.findall(r"'\s*([^']*?)\s*'", ret)

    def readlink(self, path):
        raise NotImplementedError()

    def mknod(self, path, mode, dev):
        raise NotImplementedError()

    def rmdir(self, path):
        self.eval("os", "rmdir('{}')".format(path))

    def mkdir(self, path, mode):
        self.eval("os", "mkdir('{}')".format(path))

    def statfs(self, path):
        pattern = r'\((?P<f_bsize>\d+), ' \
                  r'(?P<f_frsize>\d+), ' \
                  r'(?P<f_blocks>\d+), ' \
                  r'(?P<f_bfree>\d+), ' \
                  r'(?P<f_bavail>\d+), ' \
                  r'(?P<f_files>\d+), ' \
                  r'(?P<f_ffree>\d+), ' \
                  r'(?P<f_avail>\d+), ' \
                  r'(?P<f_flag>\d+), ' \
                  r'(?P<f_namemax>\d+)\)'
        ret = self.eval("os", "statvfs('{}')".format(path))
        stats = re.match(pattern, ret).groupdict()
        return {k: int(v) for k, v in stats.items()}

    def unlink(self, path):
        raise NotImplementedError()

    def symlink(self, name, target):
        raise NotImplementedError()

    def rename(self, old, new):
        raise NotImplementedError()

    def link(self, target, name):
        raise NotImplementedError()

    def utimens(self, path, times=None):
        raise NotImplementedError()

    def destroy(self, path):
        fhs = list(self.file_handles.keys())
        for fh in fhs:
            self.release(None, fh)

        self.board.exit_raw_repl()
        self.board.close()

    #
    # File methods
    #

    def open(self, path, flags):
        file_handle = 0
        while file_handle in self.file_handles:
            file_handle += 1
        var = "fh_{}".format(file_handle)

        if flags & (os.O_RDONLY + os.O_APPEND):
            mode = "a"
        elif flags & os.O_RDONLY:
            mode = "r"
        elif flags & (os.O_RDWR + os.O_CREAT):
            mode = "w+"
        elif flags & os.O_RDWR:
            mode = "r+"
        elif flags & (os.O_WRONLY + os.O_TRUNC + os.O_CREAT):
            mode = "w"
        elif flags & os.O_APPEND:
            mode = "a+"
        else:
            mode = "w+"

        self.create_var(var, 'open("{}", "{}")'.format(path, mode))
        self.file_handles[file_handle] = var
        return file_handle

    def create(self, path, mode, fi=None):
        return self.open(path, os.O_RDWR + os.O_CREAT)

    def read(self, path, length, offset, fh):
        var = self.file_handles[fh]
        self.eval(var, "seek({}, 0)".format(offset))
        w = self.eval(var, "read({})".format(length)).encode('ascii')
        return w.replace(b"\r\n", b"\n")

    def write(self, path, buf, offset, fh):
        raise NotImplementedError()

    def truncate(self, path, length, fh=None):
        if length is 0:
            fh = self.open(path, os.O_RDWR)
            self.release(path, fh)
        else:
            raise NotImplementedError()

    def flush(self, path, fh):
        var = self.file_handles[fh]
        self.eval(var, "flush()")

    def release(self, path, fh):
        var = self.file_handles[fh]
        self.eval(var, "close()")
        del self.file_handles[fh]

    def fsync(self, path, fdatasync, fh):
        raise NotImplementedError()


def main(device, mntpoint):
    FUSE(MpyFuse(device), mntpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])