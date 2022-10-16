from dataclasses import dataclass
from distutils.log import info
import hashlib
import json
from multiprocessing.sharedctypes import Value
import os
from struct import *
from tempfile import NamedTemporaryFile
from typing import List, Type


@dataclass
class BANKInfo:
    symbol: str = "_"
    file_id: int = None
    unknown_1: int = None
    wa: List = None

    def __init__(self, *kwargs):
        if kwargs:
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
            if info_block.symbols["file"][d["file_id"]] != "":
                d["file_id"] = f"SBNK/{info_block.symbols['file'][d['file_id']]}.sbnk"
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
        if self.file_id is None:
            return 0
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
            swar_name = info_block.wavearc.records[swar_id].symbol
            d["swar"] = f"SWAR/{swar_name}.swar"
            try:
                d["swav"] = info_block.swar_contents[swar_name][d["swav"]]
            except KeyError:
                pass
    except IndexError:
        pass
    return d


def inst_unformat(self, info_block, id):
    d = self.__dict__.copy()
    count = tuple(i.file_id for i in info_block.bank.records if i.file_id == id)
    if len(count) != 1:
        return d  # assume that the sbnk file is referenced by more than one entry
    record = tuple(i.file_id for i in info_block.bank.records).index(id)
    if isinstance(d["swar"], str) and isinstance(d["swav"], str):
        d["swav"] = info_block.swar_contents[d["swar"]].index(d["swav"])
    if isinstance(d["swar"], str):
        wa_ref = []
        for w in info_block.bank.records[record].wa:
            try:
                wa_ref.append(info_block.symbols["file"][info_block.wavearc.records[info_block.ids[info_block.symbols["wavearc"][w]]].file_id])
            except KeyError:
                wa_ref.append(-1)
        d["swar"] = wa_ref.index(d["swar"])
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
    def __init__(self, data, _id):
        self.id = _id
        self.name = "SBNK"
        self.data = data
        self.header = None
        self.header_struct = "<4sIIHH4sI32sI"

    def parse_header(self):
        self.header = SBNKHeader(*unpack_from(self.header_struct, self.data))
        
    def dump(self, name, folder, info_block):
        if not self.header:
            self.parse_header()
        with open(f"{folder}/{self.name}/{name}.{self.name.lower()}", "wb") as outfile:
            outfile.write(self.data)

    def add_inst(self, folder, rec, info_block):
        try:  # don't include the swar in the MD5, it will not be in the file
            del rec["swar"]
        except TypeError:
            pass
        inst_md5 = hashlib.md5(json.dumps(rec, sort_keys=True).encode('utf-8')).hexdigest()
        try:
            inst_file = info_block.inst_md5_list.index(inst_md5)
            inst_name = info_block.inst_list[inst_file]
        except ValueError:
            inst_file = len(info_block.inst_md5_list)
            info_block.inst_md5_list.append(inst_md5)
            try:
                inst_name = f"INST/{rec['swav'].strip('~')[5:-5]}.json"
                if inst_name in info_block.inst_list:
                    index = 1
                    inst_name_part = f"INST/{rec['swav'].strip('~')[5:-5]}"
                    while True:
                        inst_name = f"{inst_name_part}_{index}.json"
                        if inst_name not in info_block.inst_list:
                            break
                        index += 1
            except (AttributeError, TypeError):
                if isinstance(rec, dict):  # swavs with a ID instead of a name (maybe 8-bit synth)
                    inst_name = f"INST/unknown_{inst_file}.json"
                else:
                    inst_name = f"INST/unused_{inst_file}.json"
            info_block.inst_list.append(inst_name)
        with open(f"{folder}/{self.name}/{inst_name}", "w") as outfile:
            outfile.write(json.dumps(rec, indent=4))
        return inst_name

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
                pointers[-1] = tuple([pointers[-1][0], 0xFFFFFFFF, pointers[-1][2]])
            offset += 4
        ordered_pointers = list(set(pointers))
        ordered_pointers.sort(key=lambda tup: tup[1])
        records = []
        indexed_pointers = []
        if ordered_pointers:
            indexed_pointers.append(ordered_pointers[0][1])
        expected_offset = offset
        os.makedirs(f"{folder}/{self.name}/INST", exist_ok=True)
        for type, offset, _ in ordered_pointers:
            if offset == 0xFFFFFFFF:
                continue
            if expected_offset != offset:  # This grabs unused data (BW has this)
                #raise ValueError(f"{name}: Expected offset {expected_offset}, got {offset}")
                rec = unpack_from(f"<{'B' * (offset - expected_offset)}", self.data, offset=expected_offset)
                records.append({"unused": self.add_inst(folder, rec, info_block)})
                if indexed_pointers[-1] != expected_offset:
                    indexed_pointers.append(expected_offset)
            rec = {}
            if indexed_pointers[-1] != offset:
                indexed_pointers.append(offset)
            record_struct = "<HHBBBBBB"
            count = 1
            inst_type = SBNKInst
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
                r_inst = inst_format(inst_type(*unpack_from(record_struct, self.data, offset=offset)), info_block, self.id)
                rec["instruments"].append({"swar": r_inst["swar"], "inst":self.add_inst(folder, r_inst, info_block)})
                offset += record_size
            records.append(rec)
            expected_offset = offset
        if self.header.file_size - expected_offset > 3:  # This grabs unused data at the end (B2W2 has this)
            #raise ValueError(f"{name}: Expected size {self.header.file_size}, got {expected_offset}")
            rec = unpack_from(f"<{'B' * (self.header.file_size - expected_offset)}", self.data, offset=expected_offset)
            records.append({"unused": self.add_inst(folder, rec, info_block)})
            if indexed_pointers[-1] != expected_offset:
                indexed_pointers.append(expected_offset)
        for i in output_json["pointers"]:
            try:
                i["index"] = indexed_pointers.index(i["index"])
            except KeyError:
                pass
        output_json["records"] = tuple(i for i in records)
        with open(f"{folder}/{self.name}/{name}.json", "w") as outfile:
            outfile.write(json.dumps(output_json, indent=4))

    @classmethod
    def build(cls, name, folder, info_block, _id):
        with open(f"{folder}/{name.replace('.sbnk', '.json')}", "r") as infile:
            json_data = json.loads(infile.read())
        with NamedTemporaryFile() as output_file:
            #print(json_data["records"][0]["instruments"][0]["swav"])
            pointers = []
            #print(len(pointers))
            cls = SBNK(output_file, 0)
            cls.header = SBNKHeader(b'SBNK', 0x0100FEFF, 0, 16, 1, b'DATA', 0, b'\x00', len(json_data["pointers"]))
            cls.data.write(pack(cls.header_struct, *cls.header.__dict__.values()))
            cls.data.write(b'\x00\x00\x00\x00' * len(json_data["pointers"]))
            offset = cls.data.tell()
            for index, record in enumerate(json_data["records"]):
                pointers.append(offset)
                if "unused" in record.keys():
                    with open(f"{folder}/SBNK/{record['unused']}", "r") as inst_file:
                        cls.data.write(bytearray(json.loads(inst_file.read())))
                else:
                    count = 1
                    inst_type = SBNKInst
                    record_struct = "<HHBBBBBB"
                    try:
                        range_low = record["range_low"]
                        range_high = record["range_high"]
                        count = (range_high - range_low) + 1
                        cls.data.write(pack("<BB", range_low, range_high))
                        inst_type = SBNKInstMulti
                        record_struct = "<HHHBBBBBB"
                    except KeyError:
                        pass
                    try:
                        keysplits = record["keysplits"]
                        count = len(tuple(i for i in keysplits if i))
                        cls.data.write(pack("<BBBBBBBB", *keysplits))
                        inst_type = SBNKInstMulti
                        record_struct = "<HHHBBBBBB"
                    except KeyError:
                        pass
                    if count != len(record["instruments"]):
                        raise ValueError(f"Unexpected count of instruments for record {index}")
                    for rec in record["instruments"]:
                        with open(f"{folder}/SBNK/{rec['inst']}", "r") as inst_file:
                            temp_rec = json.loads(inst_file.read())
                            rec.update(temp_rec)
                            del rec["inst"]
                        if inst_type == SBNKInstMulti:
                            if "unknown" not in rec.keys():
                                rec["unknown"] = 1
                        rec_struct = inst_unformat(inst_type(**rec), info_block, _id)
                        cls.data.write(pack(record_struct, *rec_struct.values()))
                offset = cls.data.tell()
            # pad to 0x04
            offset = cls.data.tell()
            offset_pad = (offset + 3) & 0xFFFFFFFC
            cls.data.write(b'\x00' * (offset_pad - offset))
            cls.header.file_size = cls.data.tell()
            cls.header.block_size = cls.header.file_size - 16
            cls.data.seek(0)
            cls.data.write(pack(cls.header_struct, *cls.header.__dict__.values()))
            for pointer in json_data["pointers"]:
                if pointer == {}:
                    cls.data.write(pack("<BHB", 0, 0, 0))
                else:
                    if "reserved" not in pointer.keys():
                        pointer["reserved"] = 0
                    pointer["index"] = pointers[pointer["index"]]
                    cls.data.write(pack("<BHB", *pointer.values()))
            cls.data.seek(0)
            cls.data.flush()
            with open(f"{folder}/{name}", "wb") as converted_file:
                converted_file.write(output_file.read())
        return cls