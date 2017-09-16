import re
import sys

import serial


class MpyDeviceError(Exception):
    pass


class MpyDevice(object):
    CTRL_A = b'\x01'
    CTRL_B = b'\x02'
    CTRL_C = b'\x03'
    CTRL_D = b'\x04'

    ENTER_REPL = CTRL_B
    ENTER_RAW_REPL = CTRL_A
    SOFT_REBOOT = CTRL_D
    COMMAND_TERMINATION = CTRL_D

    FLUSH_SIZE = 1024

    DEFAULT_BAUDRATE = 115200

    def __init__(self, dev):
        self.dev = dev
        self.serial = None
        self.mpy_version = None
        self.git_hash = None
        self.build_date = None
        self.board_type = None
        self.connect()

    def connect(self):
        self.serial = serial.Serial(self.dev,
                                    baudrate=MpyDevice.DEFAULT_BAUDRATE,
                                    timeout=0)
        self.flush()

    def flush(self):
        while self.serial.read(MpyDevice.FLUSH_SIZE) != b'':
            pass

    def read_until(self, until, output=None):
        buf = b''
        while buf[-len(until):] != until.encode():
            c = self.serial.read(1)
            if output:
                print(c.decode('utf-8'), file=output, end='')
                output.flush()
            buf += c
        return buf[:-len(until)].decode('utf8')

    def readline(self):
        return self.read_until('\r\n')

    def readlines(self, num):
        for _ in range(num):
            yield self.readline()

    def set_info_from_string(self, s):
        pattern = r'MicroPython v(?P<version>\d+\.\d+\.\d+-\d+)' \
                  r'-(?P<git_hash>.{9}) ' \
                  r'on (?P<date>\d{4}-\d{2}-\d{2}); ' \
                  r'(?P<board>.+)'
        match = re.match(pattern, s)
        if match:
            self.mpy_version = match.group('version')
            self.git_hash = match.group('git_hash')
            self.build_date = match.group('date')
            self.board_type = match.group('board')
            return True
        return False

    def enter_repl(self):
        self.serial.write(MpyDevice.ENTER_REPL)
        lines = self.readlines(4)

        while not self.set_info_from_string(next(lines)):
            pass

        if next(lines) != 'Type "help()" for more information.':
            raise MpyDeviceError('Enter REPL response mismatch')

        if next(lines) != '>>> ':
            raise MpyDeviceError('Error starting REPL')

    def enter_raw_repl(self):
        self.serial.write(MpyDevice.ENTER_RAW_REPL)
        self.read_until('raw REPL; CTRL-B to exit\r\n>')

    def close(self):
        self.serial.close()

    def __enter__(self):
        self.enter_raw_repl()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def exec(self, command, output=None):
        self.serial.write(command.encode() + MpyDevice.COMMAND_TERMINATION)
        self.read_until('OK', output=None)
        ret = self.read_until('\x04', output=output)
        err = self.read_until('\x04', output=None)
        if err:
            raise MpyDeviceError(err)
        return ret

    def eval(self, expression, output=None):
        ret = self.exec('print({})'.format(expression), output=output)
        ret = ret.strip()
        return ret

    def execfile(self, filename, output=sys.stdout):
        return self.exec('exec(open("{}").read())\x04'.format(filename),
                         output=output)
