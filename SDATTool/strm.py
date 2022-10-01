from dataclasses import dataclass
from struct import *


@dataclass
class STRMInfo:
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
