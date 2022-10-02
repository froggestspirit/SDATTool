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

    def format(self, info_block):
        d = self.__dict__.copy()
        try:
            if info_block.symbols[d["file_id"]] != "":
                d["file_id"] = f"STRM/{info_block.symbols[d['file_id']]}.strm"
        except IndexError:
            pass
        try:
            if info_block.player.records[d["ply"]].symbol != "":
                d["ply"] = info_block.player.records[d["ply"]].symbol
        except IndexError:
            pass
        return d
