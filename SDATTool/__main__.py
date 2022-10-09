#!/usr/bin/python3
# SDAT-Tool by FroggestSpirit
version = "2.0.2"
# Unpacks and builds SDAT files
# Make backups, this can overwrite files without confirmation

import os
import time
import argparse

from nds import NDS
from sdat import SDAT


def unpack(args):  # Unpack
    print("Unpacking...")
    with open(args.SDATfile, "rb") as infile:
        data = infile.read()
    sdat = SDAT(memoryview(data), 0)
    sdat.parse_header()
    os.makedirs(args.folder, exist_ok=True)
    sdat.dump(args.folder)


def build(args):  # Build
    print("Building SDAT...")
    with open(f"{args.SDATfile}", "wb") as outfile:
        sdat = SDAT(outfile)
        sdat.build(args.folder)


def extract(args):  # Extract SDAT from NDS
    print("Searching for SDAT...")
    with open(args.SDATfile, "rb") as infile:
        data = infile.read()
    nds = NDS(data)
    nds.parse_header()
    os.makedirs(args.folder, exist_ok=True)
    nds.extract(args.folder)


def main():
    parser = argparse.ArgumentParser(description=f"SDAT-Tool {version}: Unpack/Pack NDS SDAT Files")
    parser.add_argument("SDATfile")
    parser.add_argument("folder", nargs="?")
    mode_grp = parser.add_mutually_exclusive_group(required=True)
    mode_grp.add_argument("-u", "--unpack", dest="mode", action="store_const", const=unpack)
    mode_grp.add_argument("-b", "--build", dest="mode", action="store_const", const=build)
    mode_grp.add_argument("-e", "--extract", dest="mode", action="store_const", const=extract)
    args = parser.parse_args()

    if not args.folder:
        args.folder = ".".join(args.SDATfile.lower().split(".")[:-1])
    if args.SDATfile.lower() == args.folder.lower():
        raise ValueError("Input and output cannot match")

    ts = time.time()
    args.mode(args)
    ts2 = time.time() - ts
    print(f"Done: {ts2}s")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        raise Exception(e)
