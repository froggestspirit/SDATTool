#!/usr/bin/python3
# SDAT-Tool by FroggestSpirit
version = "2.0.0"
# Unpacks and builds SDAT files
# Make backups, this can overwrite files without confirmation

import os
import time
import argparse

from sdat import SDAT


def unpack(args):  # Unpack
    print("Unpacking...")
    with open(args.SDATfile, "rb") as infile:
        data = infile.read()
    sdat = SDAT(memoryview(data), 0)
    os.makedirs(args.folder, exist_ok=True)
    sdat.dump(args.folder)


def build(args):  # Build
    pass


def main():
    parser = argparse.ArgumentParser(description=f"SDAT-Tool {version}: Unpack/Pack NDS SDAT Files")
    parser.add_argument("SDATfile")
    parser.add_argument("folder", nargs="?")
    mode_grp = parser.add_mutually_exclusive_group(required=True)
    mode_grp.add_argument("-u", "--unpack", dest="mode", action="store_false")
    mode_grp.add_argument("-b", "--build", dest="mode", action="store_true")
    args = parser.parse_args()

    if not args.folder:
        args.folder = ".".join(args.SDATfile.lower().split(".")[:-1])
    if args.SDATfile.lower() == args.folder.lower():
        raise ValueError("Input and output cannot match")

    ts = time.time()
    if not args.mode:
        unpack(args)
    else:
        build(args)
    ts2 = time.time() - ts
    print(f"Done: {ts2}s")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        raise Exception(e)
