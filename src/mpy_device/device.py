import re
import sys

import serial


class MpyDeviceError(Exception):
    pass


class Device(object):
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
    def connect(self):
        raise NotImplementedError()

    def flush(self):
        raise NotImplementedError()

    def enter_raw_repl(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()

    def __enter__(self):
        self.enter_raw_repl()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def exec(self, command, output=None):
        raise NotImplementedError()

    def eval(self, expression, output=None):
        raise NotImplementedError()

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
