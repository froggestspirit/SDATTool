from dataclasses import dataclass
from struct import *


@dataclass
class STRMInfo:
    symbol: str
    file_id: int
    unknown_1: int
    vol: int
    pri: int
    ply: int
    reserved_1: int
    reserved_2: int
    reserved_3: int
    reserved_4: int
    reserved_5: int

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
            if info_block.symbols[d["file_id"]] != "":
                d["file_id"] = f"STRM/{info_block.symbols[d['file_id']]}.strm"
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
        info_file.data.write(pack("<HHBBBBBBBB", *(self.__dict__[i] for i in self.__dict__ if i != 'symbol')))
        return calcsize("<HHBBBBBBBB")