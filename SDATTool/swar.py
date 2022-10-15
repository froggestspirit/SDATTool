from dataclasses import dataclass
import hashlib
import json
import os
from struct import *
from tempfile import NamedTemporaryFile


@dataclass
class WAVEARCInfo:
    symbol: str = "_"
    file_id: int = None
    unknown_1: int = None

    def unformat(self, info_block, file_order):
        try:
            self.file_id = file_order.index(self.file_id)
        except ValueError:
            if isinstance(self.file_id, str):
                raise FileNotFoundError(f"File not found: {self.file_id}")
        
    def format(self, info_block):
        d = self.__dict__.copy()
        try:
            if info_block.symbols["file"][d["file_id"]] != "":
                d["file_id"] = f"SWAR/{info_block.symbols['file'][d['file_id']]}.swar"
        except IndexError:
            pass
        return d

    @classmethod
    def unpack(cls, index, mem_view):
        return cls(f"wavearc_{index:04}", *unpack_from("<HH", mem_view))

    def pack(self, info_file) -> int:
        if self.file_id is None:
            return 0
        info_file.data.write(pack("<HH", self.file_id, self.unknown_1))
        return calcsize("<HH")


@dataclass
class SWAVHeader:
    type: bytes
    magic: bytes
    file_size: int
    size: int
    blocks: int
    block_type: bytes
    block_size: int


@dataclass
class SWAVInfo:
    wave_type: int
    loop: int
    sample_rate: int
    time: int
    loop_offset: int
    non_loop_len: int


class SWAV:
    def __init__(self, data):
        self.name = "SWAV"
        self.data = data
        self.wav_data = None
        self.header = None
        self.header_struct = "<4sIIHH4sI"
        self.info = None
        self.info_struct = "<BBHHHI"

    def parse_header(self):
        self.header = SWAVHeader(*unpack_from(self.header_struct, self.data))
        
    def build_header(self):
        wav_len = (self.info.non_loop_len + self.info.loop_offset) * 4
        self.header = SWAVHeader(b'SWAV', 0x0100FEFF, 0, 16, 1, b'DATA', 0)
        self.header.file_size = wav_len + calcsize(self.header_struct) + calcsize(self.info_struct)
        self.header.block_size = self.header.file_size - 16
        self.wav_data = memoryview(self.data[:self.header.block_size - 8])
        
    def extract(self, name, folder, info_block):
        if not self.header:
            self.info = SWAVInfo(*unpack_from(self.info_struct, self.data))
        if not self.header:
            self.build_header()
        md5 = hashlib.md5(self.wav_data).hexdigest()
        try:
            return info_block.swav_md5[md5]
        except KeyError:
            pass
        os.makedirs(f"{folder}/SWAR/{self.name}", exist_ok=True)
        with open(f"{folder}/SWAR/{name}", "wb") as outfile:
            outfile.write(pack(self.header_struct, *(self.header.__dict__[i] for i in self.header.__dict__)))
            outfile.write(self.wav_data)
        info_block.swav_md5[md5] = name
        return name


@dataclass
class SWARHeader:
    type: bytes
    magic: bytes
    file_size: int
    size: int
    blocks: int
    block_type: bytes
    block_size: int
    reserved: bytes
    count: int


class SWAR:
    def __init__(self, data, _id):
        self.id = _id
        self.name = "SWAR"
        self.data = data
        self.header = None
        self.header_struct = "<4sIIHH4sI32sI"

    def parse_header(self):
        self.header = SWARHeader(*unpack_from(self.header_struct, self.data))
        
    def dump(self, name, folder, info_block):
        if not self.header:
            self.parse_header()
        with open(f"{folder}/{self.name}/{name}.{self.name.lower()}", "wb") as outfile:
            outfile.write(self.data)

    def convert(self, name, folder, info_block):
        if not self.header:
            self.parse_header()
            offset = calcsize(self.header_struct)
        filenames = []
        mapped_names = None
        try:
            with open(f"{folder}/{self.name}/{name}.txt", "r") as mapped_file:
                mapped_names = tuple(mapped_file.read().split("\n"))
        except FileNotFoundError:
            pass
        for i in range(self.header.count):
            pointer, = unpack_from("<I", self.data, offset=offset)
            offset += 4
            swav = SWAV(memoryview(self.data[pointer:]))
            swav_name = f"SWAV/{self.id}_{i}.swav"
            if mapped_names:
                swav_name = mapped_names[i]
            new_filename = swav.extract(swav_name, folder, info_block)
            while True:
                if new_filename not in filenames:  # Workaround to keep the correct index if a swar has duplicate swavs
                    break
                new_filename = f"{new_filename}~"
            filenames.append(new_filename)
        with open(f"{folder}/{self.name}/{name}.txt", "w") as outfile:
            outfile.write("\n".join(filenames))
        info_block.swar_contents[name] = tuple(filenames)
    
    @classmethod
    def build(cls, name, folder, info_block, _id):
        swar_folder = f"{folder}/SWAR"
        with open(f"{folder}/{name.replace('.swar', '.txt')}", "r") as infile:
            file_order = tuple(i for i in infile.read().split("\n") if i)
        info_block.swar_contents[name] = file_order
        with NamedTemporaryFile() as output_file:
            #print(json_data["records"][0]["instruments"][0]["swav"])
            pointers = []
            #print(len(pointers))
            cls = SWAR(output_file, 0)
            cls.header = SWARHeader(b'SWAR', 0x0100FEFF, 0, 16, 1, b'DATA', 0, b'\x00', len(file_order))
            cls.data.write(pack(cls.header_struct, *cls.header.__dict__.values()))
            cls.data.write(b'\x00\x00\x00\x00' * len(file_order))
            offset = cls.data.tell()
            for file in file_order:
                pointers.append(offset)
                with open(f"{swar_folder}/{file.strip('~')}", "rb") as swav_file:
                    swav_file.seek(0x18)
                    cls.data.write(swav_file.read())
                offset = cls.data.tell()
            cls.header.file_size = cls.data.tell()
            cls.header.block_size = cls.header.file_size - 16
            cls.data.seek(0)
            cls.data.write(pack(cls.header_struct, *cls.header.__dict__.values()))
            for pointer in pointers:
                cls.data.write(pack("<I", pointer))
            cls.data.seek(0)
            cls.data.flush()
            with open(f"{folder}/{name}", "wb") as converted_file:
                converted_file.write(output_file.read())
        return cls
        