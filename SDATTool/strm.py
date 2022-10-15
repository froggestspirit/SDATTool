from dataclasses import dataclass
from struct import *


@dataclass
class STRMInfo:
    symbol: str = "_"
    file_id: int = None
    unknown_1: int = None
    vol: int = None
    pri: int = None
    ply: int = None
    reserved_1: int = None
    reserved_2: int = None
    reserved_3: int = None
    reserved_4: int = None
    reserved_5: int = None

    def unformat(self, info_block, file_order):
        try:
            self.file_id = file_order.index(self.file_id)
        except ValueError:
            if isinstance(self.file_id, str):
                raise FileNotFoundError(f"File not found: {self.file_id}")
        try:
            self.ply = info_block.player2.symbols.index(self.ply)
        except ValueError:
            if isinstance(self.ply, str):
                raise ValueError(f"Definition not found: {self.ply}")
        
    def format(self, info_block):
        d = self.__dict__.copy()
        try:
            if info_block.symbols["file"][d["file_id"]] != "":
                d["file_id"] = f"STRM/{info_block.symbols['file'][d['file_id']]}.strm"
        except IndexError:
            pass
        try:
            if info_block.player2.records[d["ply"]].symbol != "":
                d["ply"] = info_block.player2.records[d["ply"]].symbol
        except IndexError:
            pass
        return d

    @classmethod
    def unpack(cls, index, mem_view):
        return cls(f"strm_{index:04}", *unpack_from("<HHBBBBBBBB", mem_view))

    def pack(self, info_file) -> int:
        if self.file_id is None:
            return 0
        info_file.data.write(pack("<HHBBBBBBBB", *(self.__dict__[i] for i in self.__dict__ if i != 'symbol')))
        return calcsize("<HHBBBBBBBB")


@dataclass
class STRMHeader:
    type: bytes
    magic: bytes
    file_size: int
    size: int
    blocks: int
    block_type: bytes
    block_size: int
    reserved: bytes
    count: int


class STRM:
    def __init__(self, data, _id):
        self.id = _id
        self.name = "STRM"
        self.data = data
        self.count = 0
        self.header = None
        self.header_struct = "<4sIIHH4sI32sI"

    def parse_header(self):
        self.header = STRMHeader(*unpack_from(self.header_struct, self.data))
        
    def dump(self, name, folder, info_block):
        if not self.header:
            self.parse_header()
        with open(f"{folder}/{self.name}/{name}.{self.name.lower()}", "wb") as outfile:
            outfile.write(self.data)

    def convert(self, name, folder, info_block):
        if not self.header:
            self.parse_header()
        with open(f"{folder}/{self.name}/{name}.{self.name.lower()}", "wb") as outfile:
            outfile.write(self.data)

    @classmethod
    def build(cls, name, folder, info_block, _id):
        pass

