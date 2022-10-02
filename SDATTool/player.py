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

    def format(self, info_block):
        d = self.__dict__.copy()
        return d


@dataclass
class PLAYER2Info:
    symbol: str
    count: int
    v: List
    reserved: List

    def __init__(self, *kwargs):
        self.symbol = kwargs[0]
        self.count = kwargs[1]
        self.v = kwargs[2:18]
        self.reserved = kwargs[18:25]

    def format(self, info_block):
        d = self.__dict__.copy()
        return d
