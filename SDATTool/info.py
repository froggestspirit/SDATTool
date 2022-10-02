from dataclasses import dataclass
import json
import os
from struct import *
from typing import Any, List
from sseq import SEQInfo, SEQARCInfo
from sbnk import BANKInfo
from swar import WAVEARCInfo
from player import PLAYERInfo, PLAYER2Info
from group import GROUPInfo
from strm import STRMInfo


records = (("seq", SEQInfo, "<HHHBBBBBB"),
           ("seqarc", SEQARCInfo, "<HH"),
           ("bank", BANKInfo, "<HHHHHH"),
           ("wavearc", WAVEARCInfo, "<HH"),
           ("player", PLAYERInfo, "<BBBBI"),
           ("group", GROUPInfo, "<I"),  # Do additional unpacking separately
           ("player2", PLAYER2Info, "<BBBBBBBBBBBBBBBBBBBBBBBB"),
           ("strm", STRMInfo, "<HHBBBBBBBB"))


@dataclass
class InfoHeader:
    type: bytes
    size: int
    seq_offset: int
    seqarc_offset: int
    bank_offset: int
    wavearc_offset: int
    player_offset: int
    group_offset: int
    player2_offset: int
    strm_offset: int


@dataclass
class InfoBlockRecord:
    count: int
    offsets: List[int] = None
    records: List[Any] = None


class InfoBlock:
    def __init__(self, data):
        self.data = data
        self.header = None
        self.seq = None
        self.seqarc = None
        self.bank = None
        self.wavearc = None
        self.player = None
        self.group = None
        self.player2 = None
        self.strm = None
        self.symbols = {}

    def parse_header(self):
        header_struct = "<4sIIIIIIIII"
        cursor = calcsize(header_struct)
        mem_view = memoryview(self.data[:cursor])
        self.header = InfoHeader(*unpack(header_struct, mem_view))
        #print(self.header)
        if self.header.type != b'INFO':
            raise ValueError("Not a valid INFO header")

    def parse_records(self, symb_block = None):
        if not self.header:
            self.parse_header()
        for record, info_class, struct in records:
            cursor = self.header.__dict__[f"{record}_offset"]
            mem_view = memoryview(self.data[cursor:])
            self.__dict__[record] = InfoBlockRecord(*unpack("<I", mem_view[:4]))
            count = self.__dict__[record].count
            mem_view = memoryview(self.data[cursor + 4:])
            self.__dict__[record].offsets = unpack(f"<{'I' * count}", mem_view[:count * 4])
            self.__dict__[record].records = []
            self.__dict__[record].symbols = []
            for i, entry in enumerate(self.__dict__[record].offsets):
                if info_class:
                    mem_view = memoryview(self.data[entry:entry + calcsize(struct)])
                    self.__dict__[record].records.append(info_class(f"{record}_{i:04}", *unpack(struct, mem_view)))
        for i, entry in enumerate(self.group.offsets):  # Unpack the groups
            self.group.records[i].entries = []
            mem_view = memoryview(self.data[entry + 4:])  # Offset and skip the count (should already have it)
            for e in range(self.group.records[i].count):
                cursor = e * 8
                self.group.records[i].entries.append(dict(zip(("type", "entry"),(unpack("<II", mem_view[cursor:cursor + 8])))))
        if symb_block:
            for record in ("seq", "seqarc", "bank", "wavearc", "strm"):
                    for i in range(self.__dict__[record].count):
                        file_id = self.__dict__[record].records[i].file_id
                        symb = symb_block.__dict__[record].records[i]
                        if file_id not in self.symbols.keys():
                            self.symbols[file_id] = symb
                        if symb == "":
                            symb = f"{record}_{i:04}"
                        self.__dict__[record].records[i].symbol = symb
            for record in ("player", "group", "player2"):
                    for i in range(self.__dict__[record].count):
                        symb = symb_block.__dict__[record].records[i]
                        if symb == "":
                            symb = f"{record}_{i:04}"
                        self.__dict__[record].records[i].symbol = symb


    def dump(self, folder:str, symb_block = None):
        info_folder = f"{folder}/info"
        if not self.header:
            self.parse_header()
        self.parse_records(symb_block)
        os.makedirs(info_folder, exist_ok=True)
        if symb_block:
            for record, _, _ in records:
                with open(f"{info_folder}/{record}.json", "w") as outfile:
                    output = []
                    for i in self.__dict__[record].records:
                        d = i.format(self)
                        output.append(d)
                    outfile.write(json.dumps(output, indent=4))
        else:
            for record, _, _ in records:
                with open(f"{info_folder}/{record}.json", "w") as outfile:
                    outfile.write(json.dumps(tuple(i.__dict__ for i in self.__dict__[record].records), indent=4))
