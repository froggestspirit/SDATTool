#!/usr/bin/python3
# SDAT-Tool by FroggestSpirit
version = "2.0.5"
# Unpacks and builds SDAT files
# Make backups, this can overwrite files without confirmation

import os
import time
import argparse
from tkinter import Button
gui_installed = True
try:
    from tkinter import Tk, ttk, filedialog, Toplevel, Listbox
except ModuleNotFoundError:
    gui_installed = False

from nds import NDS
from sdat import SDAT
import sdatplay


def unpack(args):  # Unpack
    print("Unpacking...")
    with open(args.SDATfile, "rb") as infile:
        data = infile.read()
    sdat = SDAT(args, memoryview(data), 0)
    sdat.parse_header()
    os.makedirs(args.folder, exist_ok=True)
    if args.convert:
        sdat.convert(args.folder)
    else:
        sdat.dump(args.folder)


def build(args):  # Build
    print("Building SDAT...")
    with open(f"{args.SDATfile}", "wb") as outfile:
        sdat = SDAT(args, outfile)
        sdat.build(args.folder)
    entries = []
    if args.ram_usage:
        for song in sdat.info.seq.records:
            if song.symbol == "_":
                continue
            files = []
            size = sdat.fat.records[song.file_id].size
            files.append(sdat.info.symbols["file"][song.file_id])
            bank = sdat.info.bank.records[song.bnk]
            size += sdat.fat.records[bank.file_id].size
            files.append(sdat.info.symbols["file"][bank.file_id])
            for w in bank.wa:
                if w != 0xFFFF:  # Maybe code to handle duplicates of the same swar?
                    swar = sdat.info.wavearc.records[w]
                    size += sdat.fat.records[swar.file_id].size
                    files.append(sdat.info.symbols["file"][swar.file_id])
            entries.append([size, song.symbol, files])
        entries.sort()
        for i in entries:
            print(i)


def load(args):  # Load
    print("Loading SDAT Files...")
    sdat = SDAT(args, None)
    sdat.load(args.folder)
    sdatplay.init()
    sdatplay.play(sdat.info, 1115)


def extract(args):  # Extract SDAT from NDS
    print("Searching for SDAT...")
    with open(args.SDATfile, "rb") as infile:
        data = infile.read()
    nds = NDS(data)
    nds.parse_header()
    os.makedirs(args.folder, exist_ok=True)
    nds.extract(args.folder)

class GUIMain:
    def __init__(self, root):
        self.root = root
        frm = ttk.Frame(self.root, padding=10)
        frm.grid()
        ttk.Label(frm, text=f"SDATTool v{version}").grid(column=0, row=0)
        ttk.Button(frm, text="Unpack SDAT", command=lambda: self.gui_open_sdat(False)).grid(column=0, row=1)
        ttk.Button(frm, text="Unpack and convert SDAT", command=lambda: self.gui_open_sdat(True)).grid(column=0, row=2)
        ttk.Button(frm, text="Play Song", command=lambda: self.gui_play_song()).grid(column=0, row=3)
        ttk.Button(frm, text="Build SDAT", command=lambda: self.gui_save_sdat()).grid(column=0, row=4)
        ttk.Button(frm, text="Dump SDAT from NDS", command=lambda: self.gui_open_nds()).grid(column=0, row=5)
        ttk.Button(frm, text="Quit", command=self.root.destroy).grid(column=0, row=6)

    def gui_open_sdat(self, extract_conv):
        args = argparse.Namespace()
        args.SDATfile = filedialog.askopenfilename(title = "Select input file",filetypes = (("SDAT","*.sdat"),("all files","*.*")))
        if args.SDATfile:
            args.folder = filedialog.askdirectory(title = "Select output folder (cancel to use the SDAT name)")
            args.convert = extract_conv
            args.single_sbnk = False
            if not args.folder:
                args.folder = ".".join(args.SDATfile.split(".")[:-1])
            if args.SDATfile.lower() == args.folder.lower():
                raise ValueError("Input and output cannot match")
            ts = time.time()
            unpack(args)
            ts2 = time.time() - ts
            print(f"Done: {ts2}s")

    def gui_save_sdat(self):
        args = argparse.Namespace()
        args.folder = filedialog.askdirectory(title = "Select input folder")
        args.SDATfile = filedialog.asksaveasfilename(title = "Select output file",filetypes = (("SDAT","*.sdat"),("all files","*.*")))
        if args.SDATfile and args.folder:
            args.ram_usage = False
            args.folder = ".".join(args.SDATfile.split(".")[:-1])
            if args.SDATfile.lower() == args.folder.lower():
                raise ValueError("Input and output cannot match")
            ts = time.time()
            build(args)
            ts2 = time.time() - ts
            print(f"Done: {ts2}s")

    def gui_open_nds(self):
        args = argparse.Namespace()
        args.SDATfile = filedialog.askopenfilename(title = "Select input file",filetypes = (("NDS Rom","*.nds"),("all files","*.*")))
        if args.SDATfile:
            args.convert = False
            args.folder = ".".join(args.SDATfile.split(".")[:-1])
            if args.SDATfile.lower() == args.folder.lower():
                raise ValueError("Input and output cannot match")
            ts = time.time()
            extract(args)
            ts2 = time.time() - ts
            print(f"Done: {ts2}s")

    def gui_play_song(self):
        args = argparse.Namespace()
        args.folder = filedialog.askdirectory(title = "Select Unpacked SDAT folder")
        if args.folder:
            self.player = Toplevel(self.root)
            GUIPlayer(self.player, args)
            self.player.wait_window()
            sdatplay.stop()


class GUIPlayer:
    def __init__(self, root, args):
        sdatplay.init()
        self.sdat = SDAT(args, None)
        self.sdat.load(args.folder)

        self.root = root
        self.root.focus_force()
        #ttk.Label(frm, text=f"SDATTool v{version}").grid(column=0, row=0)
        #ttk.Button(frm, text="Unpack SDAT", command=lambda: self.gui_open_sdat(False)).grid(column=0, row=1)
        listbox = Listbox(self.root, height = 32, width = 32)
        song_id = []
        for id, song in enumerate(self.sdat.info.seq.records):
            if song.symbol != "_":
                listbox.insert(id, song.symbol)
                song_id.append(id)
        btn = Button(root, text='Play', command=lambda: self.play(song_id[listbox.index(listbox.curselection())]))
 
        # Placing the button and listbox
        btn.pack(side='bottom')
        listbox.pack()

    def play(self, id):
        sdatplay.play(self.sdat.info, id)


def main():
    parser = argparse.ArgumentParser(description=f"SDAT-Tool {version}: Unpack/Pack NDS SDAT Files")
    parser.add_argument("SDATfile", nargs="?")
    parser.add_argument("folder", nargs="?")
    mode_grp = parser.add_mutually_exclusive_group()
    mode_grp.add_argument("-u", "--unpack", dest="mode", action="store_const", const=unpack)
    mode_grp.add_argument("-b", "--build", dest="mode", action="store_const", const=build)
    mode_grp.add_argument("-e", "--extract", dest="mode", action="store_const", const=extract)
    mode_grp.add_argument("-l", "--load", dest="mode", action="store_const", const=load)
    parser.add_argument("-c", "--convert", action="store_true", default=False)
    parser.add_argument("-ss", "--single-sbnk", action="store_true", default=False)
    parser.add_argument("-ru", "--ram-usage", action="store_true", default=False)
    args = parser.parse_args()

    if not args.SDATfile or not args.mode:
        print("Not enough parameters passed in, attempting to boot into GUI mode")
        if gui_installed:
            root = Tk()
            main_menu = GUIMain(root)
            root.mainloop()
        else:
            print("Tkinter not installed")
    else:
        if not args.folder:
            args.folder = ".".join(args.SDATfile.split(".")[:-1])
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
