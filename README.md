# mpy-dev-tools
development tools for micropython boards
* Mount a micropython device as fuse-filesystem
* Synchronize your sources with the micropython device
* Run Python scripts remotly on the micropython device
* Use all the tools from the command line or as modules for your own application

## Documentation
http://mpy-dev-tools.readthedocs.io/en/master/

## PyCharm integration
 * Create new Run configurations
   * Script: mpy_run.py
   * Parameter: /dev/tty.SLAB_USBtoUART app.py -s src
 * Start the run configuration to sync your src-folder with the device an execute your app remotly
