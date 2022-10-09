from dataclasses import dataclass
from struct import *
from typing import List


@dataclass
class PLAYERInfo:
    symbol: str
    unknown_1: int
    padding_1: int
    padding_2: int
    padding_3: int
    unknown_2: int

    def unformat(self, info_block, file_order):
        pass
        
    def format(self, info_block):
        d = self.__dict__.copy()
        return d

    @classmethod
    def unpack(cls, index, mem_view):
        return cls(f"player_{index:04}", *unpack_from("<BBBBI", mem_view))

    def pack(self, info_file) -> int:
        info_file.data.write(pack("<BBBBI", *(self.__dict__[i] for i in self.__dict__ if i != 'symbol')))
        return calcsize("<BBBBI")

@dataclass
class PLAYER2Info:
    symbol: str
    count: int
    v: List
    reserved: List

    def __init__(self, *kwargs):
        self.symbol = kwargs[0]
        self.count = kwargs[1]
        if isinstance(kwargs[2], list):  # todo: clean this up I guess..
            self.v = kwargs[2]
            if isinstance(kwargs[3], list):
                self.reserved = kwargs[3]
            else:
                self.reserved = kwargs[3:10]
        else:
            self.v = kwargs[2:18]
            if isinstance(kwargs[18], list):
                self.reserved = kwargs[18]
            else:
                self.reserved = kwargs[18:25]

    def unformat(self, info_block, file_order):
        pass
        
    def format(self, info_block):
        d = self.__dict__.copy()
        return d

    @classmethod
    def unpack(cls, index, mem_view):
        return cls(f"player2_{index:04}", *unpack_from("<BBBBBBBBBBBBBBBBBBBBBBBB", mem_view))

    def pack(self, info_file) -> int:
        info_file.data.write(pack("<BBBBBBBBBBBBBBBBBBBBBBBB", self.count, *self.v, *self.reserved))
        return calcsize("<BBBBBBBBBBBBBBBBBBBBBBBB")