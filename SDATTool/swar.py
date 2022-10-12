from dataclasses import dataclass
from struct import *


@dataclass
class WAVEARCInfo:
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
                d["file_id"] = f"SWAR/{info_block.symbols[d['file_id']]}.swar"
        except IndexError:
            pass
        return d

    @classmethod
    def unpack(cls, index, mem_view):
        return cls(f"wavearc_{index:04}", *unpack_from("<HH", mem_view))

    def pack(self, info_file) -> int:
        info_file.data.write(pack("<HH", self.file_id, self.unknown_1))
        return calcsize("<HH")


@dataclass
class SWARHeader:
    type: bytes
    magic: bytes
    file_size: int
    size: int
    blocks: int
    block_type: bytes
    block_size: int
    reserved: bytes
    count: int


class SWAR:
    def __init__(self, data, id):
        self.id = id
        self.name = "SWAR"
        self.data = data
        self.count = 0
        self.header = None
        self.header_struct = "<4sIIHH4sI32sI"

    def parse_header(self):
        self.header = SWARHeader(*unpack_from(self.header_struct, self.data))
        
    def convert(self, name, folder, info_block):
        if not self.header:
            self.parse_header()
        with open(f"{folder}/{self.name}/{name}.{self.name.lower()}", "wb") as outfile:
            outfile.write(self.data)
