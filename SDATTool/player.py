from dataclasses import dataclass
from struct import *


@dataclass
class PLAYERInfo:
    unknown_1: int
    padding_1: int
    padding_2: int
    padding_3: int
    unknown_2: int


@dataclass
class PLAYER2Info:
    count: int
    v1: int
    v2: int
    v3: int
    v4: int
    v5: int
    v6: int
    v7: int
    v8: int
    v9: int
    v10: int
    v11: int
    v12: int
    v13: int
    v14: int
    v15: int
    v16: int
    reserved_1: int
    reserved_2: int
    reserved_3: int
    reserved_4: int
    reserved_5: int
    reserved_6: int
    reserved_7: int
