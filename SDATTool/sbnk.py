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
        self.wa = kwargs[3:7]

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
