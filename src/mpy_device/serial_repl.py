import re
import sys

import serial


from .device import Device


class SerialRepl(Device):
    """
    micropython board interface

    This module provides a MpyDevice class to communicate with a micropython
    device. It allows to execute python code remote on the device.
.. code-block:: python

        with MpyDevice('dev/tty.SLAB_USBtoUART') as dev:
            dev.exec('import machine')
            freq = dev.eval('machine.freq()')
            dev.execfile('main.py')

    """
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
                                    baudrate=SerialRepl.DEFAULT_BAUDRATE,
                                    timeout=0)
        self.serial.write(SerialRepl.CTRL_C+SerialRepl.CTRL_C)
        self.flush()

    def flush(self):
        while self.serial.read(SerialRepl.FLUSH_SIZE) != b'':
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
        self.serial.write(SerialRepl.ENTER_REPL)
        lines = self.readlines(4)

        while not self.set_info_from_string(next(lines)):
            pass

        if next(lines) != 'Type "help()" for more information.':
            raise SerialRepl('Enter REPL response mismatch')

        if next(lines) != '>>> ':
            raise SerialRepl('Error starting REPL')

    def enter_raw_repl(self):
        self.serial.write(SerialRepl.ENTER_RAW_REPL)
        self.read_until('raw REPL; CTRL-B to exit\r\n>')

    def execfile(self, filename, output=sys.stdout):
        """
        Executes a script on the device.
        The Script must be located on the device.

        :param filename: Filename of the script to run on the device.
        :param output: File-object to redirect the output of stdout
        :return: output on stdout as string
        """
        return self.exec('exec(open("{}").read())\x04'.format(filename),
                         output=output)
