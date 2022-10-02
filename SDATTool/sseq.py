from dataclasses import dataclass
from struct import *


@dataclass
class SEQInfo:
    symbol: str
    file_id: int
    unknown_1: int
    bnk: int
    vol: int
    cpr: int
    ppr: int
    ply: int
    unknown_2: int
    unknown_3: int

    def format(self, info_block):
        d = self.__dict__.copy()
        try:
            if info_block.symbols[d["file_id"]] != "":
                d["file_id"] = f"SSEQ/{info_block.symbols[d['file_id']]}.sseq"
        except IndexError:
            pass
        try:
            if info_block.bank.records[d["bnk"]].symbol != "":
                d["bnk"] = info_block.bank.records[d["bnk"]].symbol
        except IndexError:
            pass
        try:
            if info_block.player.records[d["ply"]].symbol != "":
                d["ply"] = info_block.player.records[d["ply"]].symbol
        except IndexError:
            pass
        return d


@dataclass
class SEQARCInfo:
    symbol: str
    file_id: int
    unknown_1: int

    def format(self, info_block):
        d = self.__dict__.copy()
        try:
            if info_block.symbols[d["file_id"]] != "":
                d["file_id"] = f"SSAR/{info_block.symbols[d['file_id']]}.ssar"
        except IndexError:
            pass
        return d


@dataclass
class SSEQHeader:
    type: bytes
    magic: bytes
    file_size: int
    size: int
    blocks: int
    block_type: bytes
    block_size: int
    offset: int


class SSEQ:
    def __init__(self, data, offset:int = 0):
        self.offset = offset
        self.data = data
        self.view = None
        self.header = None

    def parse_header(self):
        header_struct = "<4sIIHH4sII"
        cursor = self.offset
        mem_view = memoryview(self.data[cursor:cursor + calcsize(header_struct)])
        cursor += calcsize(header_struct)
        self.header = SSEQHeader(*unpack(header_struct, mem_view))
        print(self.header)
        if self.header.type != b'SSEQ':
            raise ValueError("Not a valid SSEQ header")
        if self.header.magic != 0x0100FEFF:
            raise ValueError("Not a valid SSEQ header magic")
        if self.header.size != 16:
            raise ValueError("Unsupported SSEQ header size")
        if self.header.blocks != 1:
            raise ValueError("SSEQ should have 1 block")
        if self.header.block_type != b'DATA':
            raise ValueError("Not a valid DATA header")
        if self.header.block_size != (self.header.file_size - self.header.size):
            raise ValueError("Unexpected block size")
        if self.header.offset != 0x1C:
            raise ValueError("Offset isn't the expected size of 0x1C")
        self.view = memoryview(self.data[self.header.offset:])

    def dump(self, file_path:str):
        if not self.header:
            self.parse_header()

