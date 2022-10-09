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