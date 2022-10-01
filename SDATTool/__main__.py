#!/usr/bin/python3
# SDAT-Tool by FroggestSpirit
version = "2.0.0"
# Unpacks and builds SDAT files
# Make backups, this can overwrite files without confirmation

import os
import time
import argparse
import json
from shutil import copyfile

from sdat import SDAT


def unpack(args):  # Unpack
    print("Unpacking...")
    os.makedirs(args.folder, exist_ok=True)
    with open(args.SDATfile, "rb") as infile:
        data = infile.read()
    sdat = SDAT(memoryview(data), 0)
    sdat.parse_header()
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
    parser.add_argument("-o", "--optimize", dest="optimize", action="store_true", help="Remove unused and duplicate files")
    parser.add_argument("-os", "--optimize_size", dest="optimizeSize", action="store_true", help="Build Optimized for filesize")
    parser.add_argument("-or", "--optimize_ram", dest="optimizeRAM", action="store_true", help="Build Optimized for RAM")
    parser.add_argument("-ns", "--noSymbBlock", dest="noSymbBlock", action="store_true", help="Build without a SymbBlock")
    parser.add_argument("-wr", "--writeRaw", dest="writeRaw", action="store_true", help="Extract raw files")
    args = parser.parse_args()

    if args.optimizeSize or args.optimizeRAM:
        args.optimize = True

    if args.optimizeRAM & args.optimizeSize:
        raise ValueError("Cannot optimize for size and RAM")
    if args.SDATfile.lower().find(".sdat") == -1:
        raise ValueError("File is not a SDAT file")
    if not args.folder:
        args.folder = args.SDATfile.lower().replace(".sdat","")
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
