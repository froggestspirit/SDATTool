from dataclasses import dataclass, make_dataclass
import json
import os
from socket import SOCK_SEQPACKET
from struct import *
from tempfile import NamedTemporaryFile
from typing import Any, List
from info import InfoBlock
from sseq import SSEQ, SSAR
from sbnk import SBNK
from swar import SWAR
from strm import STRM


blocks = ("symb", "info", "fat", "file")
records = ("seq",
           "seqarc",
           "bank",
           "wavearc",
           "player",
           "group",
           "player2",
           "strm")

record_class = {
    "SSEQ": SSEQ,
    "SSAR": SSAR,
    "SBNK": SBNK,
    "SWAR": SWAR,
    "STRM": STRM
}


@dataclass
class SDATHeader:
    type: bytes
    magic: bytes
    file_size: int
    size: int
    blocks: int


class SDAT:
    def __init__(self, data, offset:int = 0):
        self.offset = offset
        self.data = data
        self.view = None
        self.header = None
        self.blocks = None
        self.symb = None
        self.info = None
        self.fat = None
        self.file = None
        self.header_struct = "<4sIIHH"

    def parse_header(self):
        cursor = self.offset
        mem_view = memoryview(self.data[cursor:cursor + calcsize(self.header_struct)])
        cursor += calcsize(self.header_struct)
        self.header = SDATHeader(*unpack(self.header_struct, mem_view))
        #print(self.header)
        if self.header.type != b'SDAT':
            raise ValueError("Not a valid SDAT header")
        if self.header.magic != 0x0100FEFF:
            raise ValueError("Not a valid SDAT header magic")
        if self.header.blocks not in (4, 3):
            raise ValueError(f"Unexpected number of blocks: {self.header.blocks}")
        block_struct = []
        for i in blocks[4 - self.header.blocks:]:
            block_struct.append((f"{i}_offset", int))
            block_struct.append((f"{i}_size", int))
        HeaderBlocks = make_dataclass("HeaderBlocks", fields=block_struct)
        block_struct = "II" * self.header.blocks
        mem_view = memoryview(self.data[cursor:cursor + calcsize(block_struct)])
        cursor += calcsize(block_struct)
        self.blocks = HeaderBlocks(*unpack(block_struct, mem_view))
        #print(self.blocks)
        self.view = memoryview(self.data[self.offset:self.offset + self.header.file_size])
        if self.header.blocks == 4:
            self.symb = SymbBlock(memoryview(self.view[self.blocks.symb_offset:self.blocks.symb_offset + self.blocks.symb_size]))
        self.info = InfoBlock(memoryview(self.view[self.blocks.info_offset:self.blocks.info_offset + self.blocks.info_size]))
        self.fat = FatBlock(memoryview(self.view[self.blocks.fat_offset:self.blocks.fat_offset + self.blocks.fat_size]))
        self.file = FileBlock(memoryview(self.view[self.blocks.file_offset:self.blocks.file_offset + self.blocks.file_size]), self.blocks.file_offset)

    def dump(self, folder:str):
        if not self.header:
            self.parse_header()
        if self.symb:
            self.symb.dump(folder)
        self.info.dump(folder, self.symb)
        self.file.dump(folder, self.fat, self.info)

    def convert(self, folder:str):
        if not self.header:
            self.parse_header()
        if self.symb:
            self.symb.dump(folder)
        self.info.dump(folder, self.symb)
        self.file.dump(folder, self.fat, self.info, convert=True)

    def build(self, folder:str):
        with NamedTemporaryFile() as file_block, \
             NamedTemporaryFile() as fat_block, \
             NamedTemporaryFile() as info_block, \
             NamedTemporaryFile() as symb_block:
            self.fat = FatBlock(fat_block)
            self.file = FileBlock(file_block, 0)
            self.info = InfoBlock(info_block)
            self.symb = SymbBlock(symb_block)
            self.file.build_header()
            with open(f"{folder}/files.txt", "r") as infile:
                file_order = tuple(infile.read().split("\n"))
            for _id, file in enumerate(file_order):
                self.info.symbols["file"][_id] = file
                self.info.ids[file] = _id
            offset = 0
            self.info.build(folder, file_order)
            self.symb.build(self.info)
            for type in ("SWAR", "SBNK", "SSEQ", "SSAR", "STRM"):  # extract in this order
                for _id, file in enumerate(file_order):
                    if file[:4] == type:
                        #if not os.path.exists(f"{folder}/{file}"):
                        try:
                            file_class = record_class[file[:4]].build(file, folder, self.info, _id)
                        except FileNotFoundError:
                            pass
            for _id, file in enumerate(file_order):
                size = self.file.add_file(f"{folder}/{file}")
                self.fat.add_entry(offset, size)
                offset += size
                offset = (offset + 0x1F) & 0xFFFFFFE0  # pad to 0x20
            self.file.build()
            self.fat.build()

            self.header = SDATHeader(b'SDAT', 0x0100FEFF, 0, 0, 4)
            self.data.write(pack(self.header_struct, *(self.header.__dict__[i] for i in self.header.__dict__)))
            header_size = offset = 0x38
            if self.header.blocks == 4:
                header_size = offset = 0x40
                self.data.write(pack("<II", offset, self.symb.header.size))
                offset += (self.symb.header.size + 3) & 0xFFFFFFFC
            self.data.write(pack("<II", offset, self.info.header.size))
            offset += (self.info.header.size + 3) & 0xFFFFFFFC
            self.data.write(pack("<II", offset, self.fat.header.size))
            offset += (self.fat.header.size + 3) & 0xFFFFFFFC
            file_pointer_offset = self.data.tell()  # save this for later to update
            self.data.write(pack("<II", offset, self.file.header.size))
            offset += (self.file.header.size + 3) & 0xFFFFFFFC
            self.data.write(b'\x00' * 16)  # reserved/unused space
            if self.header.blocks == 4:
                self.data.write(self.symb.data.read())
            self.data.write(self.info.data.read())

            # since files need to be aligned to 0x20, the header is written first, then padding is added
            # pad to 0x20
            offset = self.data.tell()
            offset += self.fat.header.size  # offset by the fat block size since it wasn't written yet
            offset += 12  # offset by the file block header size since it wasn't written yet
            pad_size = ((offset + 0x1F) & 0xFFFFFFE0) - offset
            self.fat.build(offset=pad_size + offset)  # rebuild the fat block with the correct file offsets
            self.data.write(self.fat.data.read())  # should be written after the padding and rebuild
            # write the file header and the alignment padding
            self.file.header.size += pad_size
            self.data.write(pack(self.file.header_struct, *(self.file.header.__dict__[i] for i in self.file.header.__dict__)))
            self.data.write(b'\x00' * pad_size)
            # add the padding to the size of the block

            self.data.write(self.file.data.read())
            self.header.size = self.data.tell()
            self.data.seek(8)
            self.data.write(pack("<IH", self.header.size, header_size))
            self.data.seek(file_pointer_offset + 4)  # rewrite the size in case it changed with padding
            self.data.write(pack("<I", self.file.header.size))
            self.data.flush()
            self.data.seek(0)



@dataclass
class SymbHeader:
    type: bytes
    size: int
    seq_offset: int
    seqarc_offset: int
    bank_offset: int
    wavearc_offset: int
    player_offset: int
    group_offset: int
    player2_offset: int
    strm_offset: int


@dataclass
class SymbBlockRecord:
    count: int
    offsets: List[int] = None
    records: List[Any] = None


class SymbBlock:
    def __init__(self, data):
        self.data = data
        self.header = None
        self.seq = None
        self.seqarc = None
        self.bank = None
        self.wavearc = None
        self.player = None
        self.group = None
        self.player2 = None
        self.strm = None
        self.header_struct = "<4sIIIIIIIII"

    def parse_header(self):
        cursor = calcsize(self.header_struct)
        mem_view = memoryview(self.data[:cursor])
        self.header = SymbHeader(*unpack(self.header_struct, mem_view))
        #print(self.header)
        if self.header.type != b'SYMB':
            raise ValueError("Not a valid SYMB header")

    def parse_records(self):
        if not self.header:
            self.parse_header()
        for record in records:
            cursor = self.header.__dict__[f"{record}_offset"]
            mem_view = memoryview(self.data[cursor:])
            self.__dict__[record] = SymbBlockRecord(*unpack("<I", mem_view[:4]))
            count = self.__dict__[record].count
            mem_view = memoryview(self.data[cursor + 4:])
            self.__dict__[record].offsets = unpack(f"<{'I' * count}", mem_view[:count * 4])
            self.__dict__[record].records = []
            for entry in self.__dict__[record].offsets:
                string = []
                if entry:
                    mem_view = memoryview(self.data[entry:])
                    index = 0
                    while True:
                        char = mem_view[index]
                        index += 1
                        if char == 0:
                            break
                        string.append(chr(char))
                self.__dict__[record].records.append("".join(string))

    def dump(self, folder:str):
        # This probably doesn't need to be dumped, it's just needed to assist with the file block
        if not self.header:
            self.parse_header()
        self.parse_records()

    def build(self, info_block):
        self.header = SymbHeader(b'SYMB', 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.data.write(pack(self.header_struct, *(self.header.__dict__[i] for i in self.header.__dict__)))
        self.data.write(b'\x00' * 24)  # reserved/unused space
        offset = self.data.tell()
        total_symb = 0
        for record in records:
            self.__dict__[record] = SymbBlockRecord(0)
            self.__dict__[record].offsets = []
            self.__dict__[record].records = []
            for symb in info_block.__dict__[record].symbols:
                total_symb += 1
                if symb and symb[0] == "_":
                    self.__dict__[record].offsets.append(0)
                else:
                    self.__dict__[record].offsets.append(offset)
                    self.__dict__[record].records.append(symb)
                    offset += len(symb) + 1
        header_offset = 8
        for record in records:
            offset = self.data.tell()
            self.data.seek(header_offset)
            self.data.write(pack("<I", offset))
            header_offset += 4
            self.data.seek(0, 2)  # seek to the end
            num_records = len(self.__dict__[record].offsets)
            self.data.write(pack("<I", num_records))
            offset = (total_symb * 4) + 32  # offset to add after sizes and offsets are written
            for i in self.__dict__[record].offsets:
                if i:
                    i += offset  # add the offset to the symbol if it's not null
                self.data.write(pack("<I", i))
        for record in records:
            for i in self.__dict__[record].records:
                self.data.write(i.encode(encoding='utf-8'))
                self.data.write(b'\x00')
        # pad to 0x4
        self.header.size = self.data.tell()
        padding = (self.header.size + 0x3) & 0xFFFFFFFC
        self.data.write(b'\x00' * (padding - self.header.size))
        self.data.seek(4)
        self.data.write(pack("<I", padding))
        self.data.flush()
        self.data.seek(0)


@dataclass
class FatEntry:
    offset: int
    size: int


@dataclass
class FatHeader:
    type: bytes
    size: int
    count: int


class FatBlock:
    def __init__(self, data):
        self.data = data
        self.header = None
        self.records = []
        self.header_struct = "<4sII"

    def parse_header(self):
        cursor = calcsize(self.header_struct)
        mem_view = memoryview(self.data[:cursor])
        self.header = FatHeader(*unpack(self.header_struct, mem_view))
        #print(self.header)
        if self.header.type != b'FAT ':
            raise ValueError("Not a valid FAT header")

    def parse_records(self):
        if not self.header:
            self.parse_header()
        for entry in range(self.header.count):
            cursor = (entry * 16) + 12
            self.records.append(FatEntry(*unpack("<II", self.data[cursor:cursor + 8])))

    def dump(self, folder: str):
        # This probably doesn't need to be dumped, it's just needed to assist with the file block
        if not self.header:
            self.parse_header()
        self.parse_records()
        with open(f"{folder}/fat.json", "w") as outfile:
            outfile.write(json.dumps(tuple(i.__dict__ for i in self.records), indent=4))

    def add_entry(self, offset: int, size: int):
        self.records.append(FatEntry(offset, size))

    def build(self, offset: int = 0):
        self.header = FatHeader(b'FAT ', 0, len(self.records))
        self.data.write(pack(self.header_struct, *(self.header.__dict__[i] for i in self.header.__dict__)))
        for rec in self.records:
            rec.offset += offset
            self.data.write(pack("<IIII", *(rec.__dict__[i] for i in rec.__dict__), 0, 0))
        # pad to 0x4
        self.header.size = self.data.tell()
        padding = (self.header.size + 0x3) & 0xFFFFFFFC
        self.data.write(b'\x00' * (padding - self.header.size))
        self.data.seek(4)
        self.data.write(pack("<I", padding))
        self.data.flush()
        self.data.seek(0)


@dataclass
class FileHeader:
    type: bytes
    size: int
    count: int


class FileBlock:
    def __init__(self, data, offset: int):
        self.data = data
        self.header = None
        self.offset = offset
        self.header_struct = "<4sII"

    def parse_header(self):
        cursor = calcsize(self.header_struct)
        mem_view = memoryview(self.data[:cursor])
        self.header = FileHeader(*unpack(self.header_struct, mem_view))
        #print(self.header)
        if self.header.type != b'FILE':
            raise ValueError("Not a valid FILE header")

    def dump(self, folder: str, fat_block: FatBlock, info_block: InfoBlock, convert: int = False):
        if not self.header:
            self.parse_header()
        fat_block.parse_records()
        file_order = []
        for i, file in enumerate(fat_block.records):
            symbol = ""
            if i in info_block.symbols["file"].keys():
                symbol = info_block.symbols["file"][i]
            if symbol == "":
                symbol = f"{i:04}"
            offset = file.offset - self.offset
            mem_view = memoryview(self.data[offset:offset + file.size])
            suffix = unpack("<4s", mem_view[:4])[0].decode()
            if suffix not in ("SSEQ", "SSAR", "SBNK", "SWAR", "STRM"):
                raise ValueError(f"Unknown file type: {suffix}")
            os.makedirs(f"{folder}/{suffix}", exist_ok=True)
            file_order.append(f"{suffix}/{symbol}.{suffix.lower()}")
        for type in ("SWAR", "SBNK", "SSEQ", "SSAR", "STRM"):  # extract in this order
            for i, file in enumerate(fat_block.records):
                symbol = ""
                if i in info_block.symbols["file"].keys():
                    symbol = info_block.symbols["file"][i]
                if symbol == "":
                    symbol = f"{i:04}"
                suffix = file_order[i][:4]
                if suffix == type:
                    offset = file.offset - self.offset
                    mem_view = memoryview(self.data[offset:offset + file.size])
                    file_type = record_class[suffix](mem_view, i)
                    if convert:
                        file_type.convert(symbol, folder, info_block)
                    else:
                        file_type.dump(symbol, folder, info_block)
        if file_order:
            with open(f"{folder}/files.txt", "w") as outfile:
                outfile.write("\n".join(file_order))

    def build_header(self):
        self.header = FatHeader(b'FILE', 0, 0)
    
    def add_file(self, filename: str) -> int:
        self.header.count += 1
        start = self.data.tell()
        with open(filename, "rb") as infile:
            self.data.write(infile.read())
        # pad to 0x20
        offset = self.data.tell()
        offset_pad = (offset + 0x1F) & 0xFFFFFFE0
        self.data.write(b'\x00' * (offset_pad - offset))
        return offset - start
            
    def build(self):
        self.header.size = self.data.tell() + 12  # Add the header size in
        self.data.flush()
        self.data.seek(0)