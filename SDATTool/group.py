from dataclasses import dataclass
from struct import *
from typing import List


info_map = {
    0x0700: "seq",
    0x0803: "seqarc",
    0x0601: "bank",
    0x0402: "wavearc"
}


@dataclass
class GROUPInfo:
    symbol: str
    count: int
    entries: List[dict] = None
        
    def format(self, info_block):
        d = self.__dict__.copy()
        for entry in d["entries"]:
            try:
                entry["entry"] = info_block.__dict__[info_map[entry["type"]]].records[entry["entry"]].symbol
            except (KeyError, IndexError):
                pass
            try:
                entry["type"] = info_map[entry["type"]]
            except (KeyError, IndexError):
                pass
        return d
