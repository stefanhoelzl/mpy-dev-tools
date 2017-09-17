import argparse

mpy_sync_parser = argparse.ArgumentParser(
    description="Synchronizes a local folder with the device file system")
mpy_sync_parser.add_argument("src", help="Local source code directory")
mpy_sync_parser.add_argument("dest", help="Micropython device mountpoint")

mpy_run_parser = argparse.ArgumentParser(
    description="Runs a script on the device")
mpy_run_parser.add_argument("device", help="Micropython Device")
mpy_run_parser.add_argument("script", help=".py-Script to run")
mpy_run_parser.add_argument("-s", "--sync_path", help="Synchronization path")

mpy_fuse_parser = argparse.ArgumentParser(
    description="Mounts a device file system")
mpy_fuse_parser.add_argument("device", help="Micropython Device")
mpy_fuse_parser.add_argument("mntpoint", help="Mounting point")
