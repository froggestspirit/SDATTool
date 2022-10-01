from dataclasses import dataclass
from struct import *


@dataclass
class BANKInfo:
    file_id: int
    unknown_1: int
    wa0: int
    wa1: int
    wa2: int
    wa3: int
