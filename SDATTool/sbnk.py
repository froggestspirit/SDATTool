from dataclasses import dataclass
import json
from struct import *
from typing import List


@dataclass
class BANKInfo:
    symbol: str
    file_id: int
    unknown_1: int
    wa: List

    def __init__(self, *kwargs):
        self.symbol = kwargs[0]
        self.file_id = kwargs[1]
        self.unknown_1 = kwargs[2]
        if isinstance(kwargs[3], list):
            self.wa = kwargs[3]
        else:
            self.wa = kwargs[3:7]

    def unformat(self, info_block, file_order):
        try:
            self.file_id = file_order.index(self.file_id)
        except ValueError:
            if isinstance(self.file_id, str):
                raise FileNotFoundError(f"File not found: {self.file_id}")
        for i, w in enumerate(self.wa):
            if w == "":
                self.wa[i] = 0xFFFF
            else:
                try:
                    self.wa[i] = info_block.wavearc.symbols.index(w)
                except ValueError:
                    if isinstance(w, str):
                        raise ValueError(f"Definition not found: {w}")
        
    def format(self, info_block):
        d = self.__dict__.copy()
        d["wa"] = list(d["wa"])
        try:
            if info_block.symbols[d["file_id"]] != "":
                d["file_id"] = f"SBNK/{info_block.symbols[d['file_id']]}.sbnk"
        except IndexError:
            pass
        for i, wa in enumerate(d["wa"]):
            try:
                if info_block.wavearc.records[wa].symbol != "":
                    d["wa"][i] = info_block.wavearc.records[wa].symbol
            except IndexError:
                pass
            if wa == 0xFFFF:
                d["wa"][i] = ""
        return d

    @classmethod
    def unpack(cls, index, mem_view):
        return cls(f"bank_{index:04}", *unpack_from("<HHHHHH", mem_view))

    def pack(self, info_file) -> int:
        info_file.data.write(pack("<HHHHHH", self.file_id, self.unknown_1, *self.wa))
        return calcsize("<HHHHHH")


@dataclass
class SBNKHeader:
    type: bytes
    magic: bytes
    file_size: int
    size: int
    blocks: int
    block_type: bytes
    block_size: int
    reserved: bytes
    count: int


def inst_format(self, info_block, id):
    d = self.__dict__.copy()
    try:
        if d["unknown"] == 1:
            del d["unknown"]  # expected to be 1, only write if it isn't
    except KeyError:
        pass
    count = tuple(i.file_id for i in info_block.bank.records if i.file_id == id)
    if len(count) != 1:
        return d  # assume that the sbnk file is referenced by more than one entry
    record = tuple(i.file_id for i in info_block.bank.records).index(id)
    try:
        swar_id = info_block.bank.records[record].wa[d["swar"]]
        if info_block.wavearc.records[swar_id].symbol != "":
            d["swar"] = f"SBNK/{info_block.wavearc.records[swar_id].symbol}.sbnk"
            #d["swar"] = f"{d['swar']}->{record}"
    except IndexError:
        pass
    return d


@dataclass
class SBNKInst:
    swav: int
    swar: int
    note: int
    attack: int
    decay: int
    sustain: int
    release: int
    pan: int


@dataclass
class SBNKInstMulti:
    unknown: int
    swav: int
    swar: int
    note: int
    attack: int
    decay: int
    sustain: int
    release: int
    pan: int


class SBNK:
    def __init__(self, data, id):
        self.id = id
        self.name = "SBNK"
        self.data = data
        self.header = None
        self.header_struct = "<4sIIHH4sI32sI"

    def parse_header(self):
        self.header = SBNKHeader(*unpack_from(self.header_struct, self.data))
        
    def dump(self, name, folder):
        if not self.header:
            self.parse_header()
        with open(f"{folder}/{self.name}/{name}.{self.name.lower()}", "wb") as outfile:
            outfile.write(self.data)

    def convert(self, name, folder, info_block):
        if not self.header:
            self.parse_header()
        offset = calcsize(self.header_struct)
        pointers = []
        output_json = {"pointers": [],
                       "records": []}
        for record in range(self.header.count):
            pointers.append(unpack_from("<BHB", self.data, offset=offset))
            output_json["pointers"].append(dict(zip(("type", "index", "reserved"),pointers[-1])))
            if not output_json["pointers"][-1]["reserved"]:
                del output_json["pointers"][-1]["reserved"]  # this is expected to be 0, only write it if it isn't
            if output_json["pointers"][-1]["type"] == 0:
                output_json["pointers"][-1] = {}
            offset += 4
        ordered_pointers = list(set(pointers))
        ordered_pointers.sort(key=lambda tup: tup[1])
        records = []
        for type, offset, _ in ordered_pointers:
            record_struct = "<HHBBBBBB"
            count = 1
            inst_type = SBNKInst
            rec = {}
            if type in (16, 17):
                record_struct = "<HHHBBBBBB"
                inst_type = SBNKInstMulti
                if type ==16:
                    rec["range_low"], rec["range_high"] = unpack_from("<BB", self.data, offset=offset)
                    count = (rec["range_high"] - rec["range_low"]) + 1
                    offset += 2
                else:  # type == 17
                    rec["keysplits"] = unpack_from("<BBBBBBBB", self.data, offset=offset)
                    count = len(tuple(i for i in rec["keysplits"] if i))
                    offset += 8
            record_size = calcsize(record_struct)
            rec["instruments"] = []
            for i in range(count):
                rec["instruments"].append(inst_format(inst_type(*unpack_from(record_struct, self.data, offset=offset)), info_block, self.id))
                offset += record_size
            records.append(rec)
        output_json["records"] = tuple(i for i in records)
        with open(f"{folder}/{self.name}/{name}.json", "w") as outfile:
            outfile.write(json.dumps(output_json, indent=4))
