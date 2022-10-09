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


records = (("seq", SEQInfo),
           ("seqarc", SEQARCInfo),
           ("bank", BANKInfo),
           ("wavearc", WAVEARCInfo),
           ("player", PLAYERInfo),
           ("group", GROUPInfo),
           ("player2", PLAYER2Info),
           ("strm", STRMInfo))


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
        self.header_struct = "<4sIIIIIIIII"

    def parse_header(self):
        cursor = calcsize(self.header_struct)
        mem_view = memoryview(self.data[:cursor])
        self.header = InfoHeader(*unpack(self.header_struct, mem_view))
        #print(self.header)
        if self.header.type != b'INFO':
            raise ValueError("Not a valid INFO header")

    def parse_records(self, symb_block = None):
        if not self.header:
            self.parse_header()
        for record, info_class in records:
            cursor = self.header.__dict__[f"{record}_offset"]
            mem_view = memoryview(self.data[cursor:])
            self.__dict__[record] = InfoBlockRecord(*unpack("<I", mem_view[:4]))
            count = self.__dict__[record].count
            mem_view = memoryview(self.data[cursor + 4:])
            self.__dict__[record].offsets = unpack(f"<{'I' * count}", mem_view[:count * 4])
            self.__dict__[record].records = []
            for i, entry in enumerate(self.__dict__[record].offsets):
                if info_class:
                    mem_view = memoryview(self.data[entry:])
                    self.__dict__[record].records.append(info_class.unpack(i, mem_view))
        if symb_block:
            for record in ("seq", "seqarc", "bank", "wavearc", "strm"):
                    for i in range(self.__dict__[record].count):
                        file_id = self.__dict__[record].records[i].file_id
                        symb = symb_block.__dict__[record].records[i]
                        if file_id not in self.symbols.keys():
                            self.symbols[file_id] = symb
                        if symb == "":
                            symb = f"_{record}_{i:04}"
                        self.__dict__[record].records[i].symbol = symb
            for record in ("player", "group", "player2"):
                    for i in range(self.__dict__[record].count):
                        symb = symb_block.__dict__[record].records[i]
                        if symb == "":
                            symb = f"_{record}_{i:04}"
                        self.__dict__[record].records[i].symbol = symb


    def dump(self, folder:str, symb_block = None):
        info_folder = f"{folder}/info"
        if not self.header:
            self.parse_header()
        self.parse_records(symb_block)
        os.makedirs(info_folder, exist_ok=True)
        if symb_block:
            for record, _ in records:
                with open(f"{info_folder}/{record}.json", "w") as outfile:
                    output = []
                    for i, rec in enumerate(self.__dict__[record].records):
                        d = {}
                        if self.__dict__[record].offsets[i]:
                            d = rec.format(self)
                        output.append(d)
                    outfile.write(json.dumps(output, indent=4))
        else:
            for record, _, _ in records:
                with open(f"{info_folder}/{record}.json", "w") as outfile:
                    outfile.write(json.dumps(tuple(i.__dict__ for i in self.__dict__[record].records), indent=4))

    def build(self, folder: str, file_order):
        self.header = InfoHeader(b'INFO', 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.data.write(pack(self.header_struct, *(self.header.__dict__[i] for i in self.header.__dict__)))
        self.data.write(b'\x00' * 24)  # reserved/unused space
        for record, info_class in records:
            self.__dict__[record] = InfoBlockRecord(0)
            self.__dict__[record].offsets = []
            self.__dict__[record].records = []
            self.__dict__[record].symbols = []
            with open(f"{folder}/info/{record}.json", "r") as infile:
                json_info = json.loads(infile.read())
            for rec in json_info:
                if rec:
                    self.__dict__[record].records.append(info_class(*rec.values()))
                    self.__dict__[record].symbols.append(self.__dict__[record].records[-1].symbol)
                else:
                    self.__dict__[record].records.append(None)
                    self.__dict__[record].symbols.append("_")
        header_offset = 8
        pointers = {}
        for record, info_class in records:
            offset = self.data.tell()
            self.data.seek(header_offset)
            self.data.write(pack("<I", offset))
            header_offset += 4
            self.data.seek(0, 2)  # seek to the end
            num_records = len(self.__dict__[record].records)
            self.data.write(pack("<I", num_records))
            pointers[record] = self.data.tell()  # store this for when the records are being written
            self.data.write(b'\x00' * (num_records * 4))
            num_records = len(self.__dict__[record].records)
            offset = self.data.tell()
            for i in range(num_records):
                if self.__dict__[record].records[i]:
                    self.__dict__[record].records[i].unformat(self, file_order)
                    self.data.seek(pointers[record])
                    self.data.write(pack("<I", offset))
                pointers[record] += 4
                self.data.seek(0, 2)  # seek to the end
                if self.__dict__[record].records[i]:
                    offset += self.__dict__[record].records[i].pack(self)
        # pad to 0x4
        self.header.size = self.data.tell()
        padding = (self.header.size + 0x3) & 0xFFFFFFFC
        self.data.write(b'\x00' * (padding - self.header.size))
        self.data.seek(4)
        self.data.write(pack("<I", padding))
        self.data.flush()
        self.data.seek(0)
