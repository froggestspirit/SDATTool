from dataclasses import dataclass, make_dataclass
import json
import os
from struct import *
from typing import Any, List
from info import InfoBlock


blocks = ("symb", "info", "fat", "file")
records = ("seq",
           "seqarc",
           "bank",
           "wavearc",
           "player",
           "group",
           "player2",
           "strm")


@dataclass
class SDATHeader:
    type: bytes
    magic: bytes
    file_size: int
    size: int
    blocks: int


class SDAT:
    def __init__(self, data, offset:int = 0):
        self.offset = offset
        self.data = data
        self.view = None
        self.header = None
        self.blocks = None
        self.symb = None
        self.info = None
        self.fat = None
        self.file = None
        self.parse_header()

    def parse_header(self):
        header_struct = "<4sIIHH"
        cursor = self.offset
        mem_view = memoryview(self.data[cursor:cursor + calcsize(header_struct)])
        cursor += calcsize(header_struct)
        self.header = SDATHeader(*unpack(header_struct, mem_view))
        #print(self.header)
        if self.header.type != b'SDAT':
            raise ValueError("Not a valid SDAT header")
        if self.header.magic != 0x0100FEFF:
            raise ValueError("Not a valid SDAT header magic")
        if self.header.blocks not in (4, 3):
            raise ValueError(f"Unexpected number of blocks: {self.header.blocks}")
        block_struct = []
        for i in blocks[4 - self.header.blocks:]:
            block_struct.append((f"{i}_offset", int))
            block_struct.append((f"{i}_size", int))
        HeaderBlocks = make_dataclass("HeaderBlocks", fields=block_struct)
        block_struct = "II" * self.header.blocks
        mem_view = memoryview(self.data[cursor:cursor + calcsize(block_struct)])
        cursor += calcsize(block_struct)
        self.blocks = HeaderBlocks(*unpack(block_struct, mem_view))
        #print(self.blocks)
        self.view = memoryview(self.data[self.offset:self.offset + self.header.file_size])
        if self.header.blocks == 4:
            self.symb = SymbBlock(memoryview(self.view[self.blocks.symb_offset:self.blocks.symb_offset + self.blocks.symb_size]))
        self.info = InfoBlock(memoryview(self.view[self.blocks.info_offset:self.blocks.info_offset + self.blocks.info_size]))
        self.fat = FatBlock(memoryview(self.view[self.blocks.fat_offset:self.blocks.fat_offset + self.blocks.fat_size]))
        self.file = FileBlock(memoryview(self.view[self.blocks.file_offset:self.blocks.file_offset + self.blocks.file_size]), self.blocks.file_offset)

    def dump(self, folder:str):
        if not self.header:
            self.parse_header()
        if self.symb:
            self.symb.dump(folder)
        self.info.dump(folder, self.symb)
        self.file.dump(folder, self.fat, self.info)


@dataclass
class SymbHeader:
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
class SymbBlockRecord:
    count: int
    offsets: List[int] = None
    records: List[Any] = None


class SymbBlock:
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

    def parse_header(self):
        header_struct = "<4sIIIIIIIII"
        cursor = calcsize(header_struct)
        mem_view = memoryview(self.data[:cursor])
        self.header = SymbHeader(*unpack(header_struct, mem_view))
        #print(self.header)
        if self.header.type != b'SYMB':
            raise ValueError("Not a valid SYMB header")

    def parse_records(self):
        if not self.header:
            self.parse_header()
        for record in records:
            cursor = self.header.__dict__[f"{record}_offset"]
            mem_view = memoryview(self.data[cursor:])
            self.__dict__[record] = SymbBlockRecord(*unpack("<I", mem_view[:4]))
            count = self.__dict__[record].count
            mem_view = memoryview(self.data[cursor + 4:])
            self.__dict__[record].offsets = unpack(f"<{'I' * count}", mem_view[:count * 4])
            self.__dict__[record].records = []
            for entry in self.__dict__[record].offsets:
                string = []
                if entry:
                    mem_view = memoryview(self.data[entry:])
                    index = 0
                    while True:
                        char = mem_view[index]
                        index += 1
                        if char == 0:
                            break
                        string.append(chr(char))
                self.__dict__[record].records.append("".join(string))

    def dump(self, folder:str):
        # This probably doesn't need to be dumped, it's just needed to assist with the file block
        if not self.header:
            self.parse_header()
        self.parse_records()


@dataclass
class FatEntry:
    offset: int
    size: int


@dataclass
class FatHeader:
    type: bytes
    size: int
    count: int


class FatBlock:
    def __init__(self, data):
        self.data = data
        self.header = None
        self.records = []

    def parse_header(self):
        header_struct = "<4sII"
        cursor = calcsize(header_struct)
        mem_view = memoryview(self.data[:cursor])
        self.header = FatHeader(*unpack(header_struct, mem_view))
        #print(self.header)
        if self.header.type != b'FAT ':
            raise ValueError("Not a valid FAT header")

    def parse_records(self):
        if not self.header:
            self.parse_header()
        for entry in range(self.header.count):
            cursor = (entry * 16) + 12
            self.records.append(FatEntry(*unpack("<II", self.data[cursor:cursor + 8])))

    def dump(self, folder:str):
        # This probably doesn't need to be dumped, it's just needed to assist with the file block
        if not self.header:
            self.parse_header()
        self.parse_records()
        with open(f"{folder}/fat.json", "w") as outfile:
            outfile.write(json.dumps(tuple(i.__dict__ for i in self.records), indent=4))


@dataclass
class FileHeader:
    type: bytes
    size: int
    count: int


class FileBlock:
    def __init__(self, data, offset:int):
        self.data = data
        self.header = None
        self.offset = offset

    def parse_header(self):
        header_struct = "<4sII"
        cursor = calcsize(header_struct)
        mem_view = memoryview(self.data[:cursor])
        self.header = FileHeader(*unpack(header_struct, mem_view))
        #print(self.header)
        if self.header.type != b'FILE':
            raise ValueError("Not a valid FILE header")

    def dump(self, folder:str, fat_block:FatBlock, info_block:InfoBlock = None):
        if not self.header:
            self.parse_header()
        fat_block.parse_records()
        file_order = []
        if not info_block:
            for i, file in enumerate(fat_block.records):
                offset = file.offset - self.offset
                mem_view = memoryview(self.data[offset:offset + file.size])
                suffix = unpack("<4s", mem_view[:4])[0].decode()
                if suffix not in ("SSEQ", "SSAR", "SBNK", "SWAR", "STRM"):
                    suffix = "bin"
                os.makedirs(f"{folder}/{suffix}", exist_ok=True)
                with open(f"{folder}/{suffix}/{i:04}.{suffix.lower()}", "wb") as outfile:
                    outfile.write(mem_view)
                file_order.append(f"{suffix}/{i:04}.{suffix.lower()}")
        else:
            for i, file in enumerate(fat_block.records):
                symbol = ""
                if i in info_block.symbols.keys():
                    symbol = info_block.symbols[i]
                if symbol == "":
                    symbol = f"{i:04}"
                offset = file.offset - self.offset
                mem_view = memoryview(self.data[offset:offset + file.size])
                suffix = unpack("<4s", mem_view[:4])[0].decode()
                if suffix not in ("SSEQ", "SSAR", "SBNK", "SWAR", "STRM"):
                    suffix = "bin"
                os.makedirs(f"{folder}/{suffix}", exist_ok=True)
                with open(f"{folder}/{suffix}/{symbol}.{suffix.lower()}", "wb") as outfile:
                    outfile.write(mem_view)
                file_order.append(f"{suffix}/{symbol}.{suffix.lower()}")
        if file_order:
            with open(f"{folder}/files.txt", "w") as outfile:
                outfile.write("\n".join(file_order))
