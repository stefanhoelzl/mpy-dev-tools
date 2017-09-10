# mpy-dev-tools
development tools for micropython boards

# Requirements
* adafruit-ampy
* fusepy

# mpy_fuse
Mounts a device file system
```
mpy_fuse.py [-h] device mntpoint
```

# mpy_sync
Synchronizes a local folder with de device file system
```
mpy_sync.py [-h] src dest
```

# mpy_run
Runs a script on the device
* mounts the device
* synchronizes the script path with the device
* excutes a script
```
mpy_run.py [-h] script device [mntpoint]
```