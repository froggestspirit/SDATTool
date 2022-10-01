from dataclasses import dataclass
from struct import *
from typing import List


@dataclass
class GROUPInfo:
    count: int
    entries: List[dict] = None
        
