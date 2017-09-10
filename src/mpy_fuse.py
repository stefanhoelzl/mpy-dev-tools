import os
import re
from multiprocessing import Process

from ampy.pyboard import Pyboard, PyboardError

from fuse import FUSE, FuseOSError, Operations


class MpyFuseOperations(Operations):
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
        self.eval("os", "remove('{}')".format(path))

    def symlink(self, name, target):
        raise NotImplementedError()

    def rename(self, old, new):
        self.eval("os", "rename('{}', '{}')".format(old, new))

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

        self.create_var(var, 'open("{}", "{}")'.format(path, mode))
        self.file_handles[file_handle] = var
        return file_handle

    def create(self, path, mode, fi=None):
        return self.open(path, os.O_RDWR + os.O_CREAT)

    def read(self, path, length, offset, fh):
        var = self.file_handles[fh]
        self.eval(var, "seek({}, 0)".format(offset))
        w = self.eval(var, "read({})".format(length)).encode('utf-8')
        return w.replace(b"\r\n", b"\n")

    def write(self, path, buf, offset, fh):
        var = self.file_handles[fh]
        self.eval(var, "seek({}, 0)".format(offset))
        cmd = 'write("""{}""")'.format(buf.decode('utf-8'))
        self.eval(var, cmd)
        return len(buf)

    def truncate(self, path, length, fh=None):
        pass

    def flush(self, path, fh):
        var = self.file_handles[fh]
        self.eval(var, "flush()")

    def release(self, path, fh):
        var = self.file_handles[fh]
        self.eval(var, "close()")
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("device", help="Micropython Device")
    parser.add_argument("mntpoint", help="Mounting point")
    args = parser.parse_args()

    fuse = MpyFuse(args.device, args.mntpoint)
    fuse.mount()

    import signal
    signal.pause()
