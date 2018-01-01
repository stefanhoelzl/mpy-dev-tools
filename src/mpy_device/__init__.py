from .apify_repl import ApifyRepl
from .serial_repl import SerialRepl
from .base_device import MpyDeviceError


class MpyDevice(object):
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

    def __new__(cls, dev):
        if ":" in dev:
            return ApifyRepl(dev)
        return SerialRepl(dev)
