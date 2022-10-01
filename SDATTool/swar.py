from dataclasses import dataclass
from struct import *


@dataclass
class WAVEARCInfo:
    file_id: int
    unknown_1: int
