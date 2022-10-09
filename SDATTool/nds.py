from dataclasses import dataclass
from struct import *


@dataclass
class NDSHeader:
    title: bytes
    game_code: bytes
    maker_code: int
    unit_code: int
    encryption: int
    capacity: int


class NDS:
    def __init__(self, data):
        self.offset = 0
        self.data = data
        self.view = None
        self.header = None
        self.fnt_offset = None
        self.fnt_size = None
        self.fat_offset = None
        self.fat_size = None
        self.header_struct = "<12s4sHBBB"
        self.folders = []
        self.files = []
        self.sdat_files = None

    def parse_header(self):
        cursor = self.offset
        mem_view = memoryview(self.data[cursor:cursor + calcsize(self.header_struct)])
        cursor += 0x40
        self.header = NDSHeader(*unpack(self.header_struct, mem_view))
        #print(self.header)
        mem_view = memoryview(self.data[cursor:cursor + calcsize("<IIII")])
        self.fnt_offset, self.fnt_size, self.fat_offset, self.fat_size = unpack("<IIII", mem_view)
        self.parse_fnt()

    def parse_fnt(self):
        mem_view = memoryview(self.data[self.fnt_offset:self.fnt_offset + self.fnt_size])
        header_offset = 0
        starting_offset, = unpack_from("<I", mem_view, offset=header_offset)
        while header_offset < starting_offset:
            offset, file_id, dirs = unpack_from("<IHH", mem_view, offset=header_offset)
            header_offset += 8
            while True:
                string_size, = unpack_from("<B", mem_view, offset=offset)
                if not string_size:
                    break
                is_dir = string_size >> 7
                string_size &= 0x7F
                offset += 1
                string = []
                while string_size:
                    char = mem_view[offset]
                    offset += 1
                    string_size -= 1
                    string.append(chr(char))
                if is_dir:
                    folder_id, = unpack_from("<H", mem_view, offset=offset)
                    offset += 2
                    self.folders.append((folder_id, "".join(string)))
                else:
                    self.files.append((file_id, "".join(string)))
                    file_id += 1
        self.sdat_files = tuple(i for i in self.files if ".sdat" in i[1])
        print(f"Found {len(self.sdat_files)} SDAT file(s)")
    
    def extract(self, folder: str):
        for file in self.sdat_files:
            print(f"Extracting {file[1]}")
            self.extract_file(folder, *file)

    def extract_file(self, folder, file_id, filename):
        mem_view = memoryview(self.data[self.fat_offset:self.fat_offset + self.fat_size])
        file_start, file_end = unpack_from("<II", mem_view, offset=(file_id * 8))
        with open(f"{folder}/{filename}", "wb") as outfile:
            outfile.write(self.data[file_start:file_end])
