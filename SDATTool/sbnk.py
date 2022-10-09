from dataclasses import dataclass
from struct import *
from typing import List


@dataclass
class BANKInfo:
    symbol: str
    file_id: int
    unknown_1: int
    wa: List

    def __init__(self, *kwargs):
        self.symbol = kwargs[0]
        self.file_id = kwargs[1]
        self.unknown_1 = kwargs[2]
        if isinstance(kwargs[3], list):
            self.wa = kwargs[3]
        else:
            self.wa = kwargs[3:7]

    def unformat(self, info_block, file_order):
        try:
            self.file_id = file_order.index(self.file_id)
        except ValueError:
            if isinstance(self.file_id, str):
                raise FileNotFoundError(f"File not found: {self.file_id}")
        for i, w in enumerate(self.wa):
            if w == "":
                self.wa[i] = 0xFFFF
            else:
                try:
                    self.wa[i] = info_block.wavearc.symbols.index(w)
                except ValueError:
                    if isinstance(w, str):
                        raise ValueError(f"Definition not found: {w}")
        
    def format(self, info_block):
        d = self.__dict__.copy()
        d["wa"] = list(d["wa"])
        try:
            if info_block.symbols[d["file_id"]] != "":
                d["file_id"] = f"SBNK/{info_block.symbols[d['file_id']]}.sbnk"
        except IndexError:
            pass
        for i, wa in enumerate(d["wa"]):
            try:
                if info_block.wavearc.records[wa].symbol != "":
                    d["wa"][i] = info_block.wavearc.records[wa].symbol
            except IndexError:
                pass
            if wa == 0xFFFF:
                d["wa"][i] = ""
        return d

    @classmethod
    def unpack(cls, index, mem_view):
        return cls(f"bank_{index:04}", *unpack_from("<HHHHHH", mem_view))

    def pack(self, info_file) -> int:
        info_file.data.write(pack("<HHHHHH", self.file_id, self.unknown_1, *self.wa))
        return calcsize("<HHHHHH")