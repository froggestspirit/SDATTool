from dataclasses import dataclass
from struct import *


@dataclass
class WAVEARCInfo:
    symbol: str
    file_id: int
    unknown_1: int

    def format(self, info_block):
        d = self.__dict__.copy()
        try:
            if info_block.symbols[d["file_id"]] != "":
                d["file_id"] = f"SWAR/{info_block.symbols[d['file_id']]}.swar"
        except IndexError:
            pass
        return d
