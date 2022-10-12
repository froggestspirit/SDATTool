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

    def unformat(self, info_block, file_order):
        try:
            self.file_id = file_order.index(self.file_id)
        except ValueError:
            if isinstance(self.file_id, str):
                raise FileNotFoundError(f"File not found: {self.file_id}")
        try:
            self.bnk = info_block.bank.symbols.index(self.bnk)
        except ValueError:
            if isinstance(self.bnk, str):
                raise ValueError(f"Definition not found: {self.bnk}")
        try:
            self.ply = info_block.player.symbols.index(self.ply)
        except ValueError:
            if isinstance(self.ply, str):
                raise ValueError(f"Definition not found: {self.ply}")
        
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

    @classmethod
    def unpack(cls, index, mem_view):
        return cls(f"seq_{index:04}", *unpack_from("<HHHBBBBBB", mem_view))

    def pack(self, info_file) -> int:
        info_file.data.write(pack("<HHHBBBBBB", *(self.__dict__[i] for i in self.__dict__ if i != 'symbol')))
        return calcsize("<HHHBBBBBB")

@dataclass
class SEQARCInfo:
    symbol: str
    file_id: int
    unknown_1: int

    def unformat(self, info_block, file_order):
        try:
            self.file_id = file_order.index(self.file_id)
        except ValueError:
            if isinstance(self.file_id, str):
                raise FileNotFoundError(f"File not found: {self.file_id}")
        
    def format(self, info_block):
        d = self.__dict__.copy()
        try:
            if info_block.symbols[d["file_id"]] != "":
                d["file_id"] = f"SSAR/{info_block.symbols[d['file_id']]}.ssar"
        except IndexError:
            pass
        return d

    @classmethod
    def unpack(cls, index, mem_view):
        return cls(f"seqarc_{index:04}", *unpack_from("<HH", mem_view))

    def pack(self, info_file) -> int:
        info_file.data.write(pack("<HH", self.file_id, self.unknown_1))
        return calcsize("<HH")

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
    def __init__(self, data, id):
        self.id = id
        self.name = "SSEQ"
        self.offset = 0
        self.data = data
        self.view = None
        self.header = None
        self.header_struct = "<4sIIHH4sII"

    def parse_header(self):
        cursor = self.offset
        mem_view = memoryview(self.data[cursor:cursor + calcsize(self.header_struct)])
        cursor += calcsize(self.header_struct)
        self.header = SSEQHeader(*unpack(self.header_struct, mem_view))
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

    def convert(self, name, folder, info_block):
        if not self.header:
            self.parse_header()
        with open(f"{folder}/{self.name}/{name}.{self.name.lower()}", "wb") as outfile:
            outfile.write(self.data)


@dataclass
class SSARHeader:
    type: bytes
    magic: bytes
    file_size: int
    size: int
    blocks: int
    block_type: bytes
    block_size: int
    offset: int
    count: int


class SSAR:
    def __init__(self, data, id):
        self.id = id
        self.name = "SSAR"
        self.offset = 0
        self.data = data
        self.view = None
        self.header = None
        self.header_struct = "<4sIIHH4sIII"

    def parse_header(self):
        cursor = self.offset
        mem_view = memoryview(self.data[cursor:cursor + calcsize(self.header_struct)])
        cursor += calcsize(self.header_struct)
        self.header = SSARHeader(*unpack(self.header_struct, mem_view))
        if self.header.type != b'SSAR':
            raise ValueError("Not a valid SSAR header")
        if self.header.magic != 0x0100FEFF:
            raise ValueError("Not a valid SSAR header magic")
        if self.header.size != 16:
            raise ValueError("Unsupported SSAR header size")
        if self.header.blocks != 1:
            raise ValueError("SSAR should have 1 block")
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

    def convert(self, name, folder, info_block):
        if not self.header:
            self.parse_header()
        with open(f"{folder}/{self.name}/{name}.{self.name.lower()}", "wb") as outfile:
            outfile.write(self.data)
