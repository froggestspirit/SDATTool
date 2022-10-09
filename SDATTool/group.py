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
        
    def unformat(self, info_block, file_order):
        for i in self.entries:
            try:
                i["entry"] = info_block.__dict__[i["type"]].symbols.index(i["entry"])
            except KeyError:
                pass
            try:
                i["type"] = tuple(info_map.keys())[tuple(info_map.values()).index(i["type"])]
            except ValueError:
                pass
        
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

    @classmethod
    def unpack(cls, index, mem_view):
        sf = cls(f"group_{index:04}", *unpack_from("<I", mem_view))
        sf.entries = []
        for e in range(sf.count):
            cursor = e * 8
            sf.entries.append(dict(zip(("type", "entry"),(unpack_from("<II", mem_view[cursor:], offset=4)))))
        return sf

    def pack(self, info_file) -> int:
        info_file.data.write(pack("<I", self.count))
        for i in self.entries:
            info_file.data.write(pack("<II", *i.values()))
        return calcsize("<I") + (calcsize("<II") * self.count)
