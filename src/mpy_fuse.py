import os
import re
from multiprocessing import Process

from fuse import FUSE, FuseOSError, Operations

from mpy_device import MpyDevice, MpyDeviceError


class MpyFuseOperations(Operations):
    def __init__(self, device):
        self.board = MpyDevice(device)
        self.board.enter_raw_repl()
        self.exec('import os')
        self.file_handles = dict()

    #
    # Mpy methods
    #
    def exec(self, command, eval=False):
        cmd = self.board.exec
        if eval:
            cmd = self.board.eval
        try:
            ret = cmd(command)
        except MpyDeviceError as e:
            pattern = re.compile(r'OSError: \[Errno (?P<error_number>\d+)\]',
                                 re.MULTILINE)
            match = pattern.search(e.args[0])
            if match:
                error_number = int(match.group('error_number'))
                raise FuseOSError(error_number)
            else:
                raise
        else:
            return ret

    #
    # Filesystem methods
    #

    def access(self, path, mode):
        pass

    def chmod(self, path, mode):
        pass

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
        ret = self.exec("os.stat('{}')".format(path), eval=True)
        attrs = re.match(pattern, ret).groupdict()
        return {k: int(v) for k, v in attrs.items()}

    def readdir(self, path, fh):
        ret = self.exec("os.listdir('{}')".format(path), eval=True)
        return re.findall(r"'\s*([^']*?)\s*'", ret)

    def readlink(self, path):
        raise NotImplementedError()

    def mknod(self, path, mode, dev):
        raise NotImplementedError()

    def rmdir(self, path):
        self.exec("os.rmdir('{}')".format(path))

    def mkdir(self, path, mode):
        self.exec("os.mkdir('{}')".format(path))

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
        ret = self.exec("os.statvfs('{}')".format(path), eval=True)
        stats = re.match(pattern, ret).groupdict()
        return {k: int(v) for k, v in stats.items()}

    def unlink(self, path):
        self.exec("os.remove('{}')".format(path))

    def symlink(self, name, target):
        raise NotImplementedError()

    def rename(self, old, new):
        self.exec("os.rename('{}', '{}')".format(old, new))

    def link(self, target, name):
        raise NotImplementedError()

    def utimens(self, path, times=None):
        raise NotImplementedError()

    def destroy(self, path):
        fhs = list(self.file_handles.keys())
        for fh in fhs:
            self.release(None, fh)

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
        elif flags == os.O_RDONLY:
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

        self.exec('{} = open("{}", "{}")'.format(var, path, mode))
        self.file_handles[file_handle] = var
        return file_handle

    def create(self, path, mode, fi=None):
        return self.open(path, os.O_RDWR + os.O_CREAT)

    def read(self, path, length, offset, fh):
        var = self.file_handles[fh]
        self.exec("{}.seek({}, 0)".format(var, offset))
        w = self.exec("{}.read({})".format(var, length), eval=True).encode('utf-8')
        return w.replace(b"\r\n", b"\n")

    def write(self, path, buf, offset, fh):
        var = self.file_handles[fh]
        self.exec("{}.seek({}, 0)".format(var, offset))
        self.exec('{}.write("""{}""")'.format(var, buf.decode('utf-8')))
        return len(buf)

    def truncate(self, path, length, fh=None):
        pass

    def flush(self, path, fh):
        var = self.file_handles[fh]
        self.exec("{}.flush()".format(var))

    def release(self, path, fh):
        var = self.file_handles[fh]
        self.exec("{}.close()".format(var))
        del self.file_handles[fh]

    def fsync(self, path, fdatasync, fh):
        self.flush(path, fh)


class MpyFuse(object):
    def __init__(self, device, mntpoint):
        self.process = None
        self.mntpoint = mntpoint
        self.device = device

    def __repr__(self):
        return 'MpyFuse(device="{}", mntpoint="{}", mounted={})'\
            .format(self.device, self.mntpoint, self.process is not None)

    def mount(self):
        fuse_args = (MpyFuseOperations(self.device), self.mntpoint)
        fuse_kwargs = {'nothreads': True, 'foreground': True}

        self.process = Process(target=FUSE, args=fuse_args, kwargs=fuse_kwargs)
        self.process.daemon = True
        self.process.start()

    def unmount(self):
        self.process.terminate()
        self.process = None

if __name__ == '__main__':
    args = mpy_fuse_parser.parse_args()

    fuse = MpyFuse(args.device, args.mntpoint)
    fuse.mount()

    import signal
    signal.pause()
