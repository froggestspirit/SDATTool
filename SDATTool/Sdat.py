import os
import hashlib
from const import itemHeader, itemExt, itemString, infoBlockGroup, infoBlockGroupType
from Sseq import sseqCmdArgs, sseqCmdName, sseqNote
from const import infoBlockGroup, infoBlockGroupType, itemString
from util import read_long, read_short, read_byte, read_item_name, read_filename, \
                 append_long, append_short, append_byte, \
                 write_long, write_short, write_byte, get_string

LONG = -4
SHORT = -2
BYTE = -1
SEQ = 0
SEQARC = 1
BANK = 2
WAVARC = 3
PLAYER = 4
GROUP = 5
PLAYER2 = 6
STRM = 7
FILE = 8


class SDAT:
    class InfoBlock:
        class SEQInfo:
            def __init__(self, sdat, name, dict=None):
                if dict:
                    self.name = dict["name"]
                    if self.name != "":
                        self.fileName = dict["fileName"]
                        self.unkA = dict["unkA"]
                        self.bnk = dict["bnk"]
                        self.vol = dict["vol"]
                        self.cpr = dict["cpr"]
                        self.ppr = dict["ppr"]
                        self.ply = dict["ply"]
                        self.unkB = dict["unkB"]
                else:
                    self.name = name
                    if self.name != "":
                        self.fileName = read_filename(sdat)
                        self.unkA = read_short(sdat)
                        self.bnk = read_item_name(sdat, BANK)
                        self.vol = read_byte(sdat)
                        self.cpr = read_byte(sdat)
                        self.ppr = read_byte(sdat)
                        self.ply = read_item_name(sdat, PLAYER)
                        self.unkB = [None] * 2
                        for i in range(2):
                            self.unkB[i] = read_byte(sdat)
            def write(self, sdat):
                if self.name != "":
                    append_short(sdat, sdat.names[FILE].index(self.fileName))
                    append_short(sdat, self.unkA)
                    append_short(sdat, [i.name for i in sdat.infoBlock.bankInfo].index(self.bnk))
                    append_byte(sdat, self.vol)
                    append_byte(sdat, self.cpr)
                    append_byte(sdat, self.ppr)
                    append_byte(sdat, [i.name for i in sdat.infoBlock.playerInfo].index(self.ply))
                    for i in range(2):
                        append_byte(sdat, self.unkB[i])
        class SEQARCInfo:
            def __init__(self, sdat, name, dict=None):
                if dict:
                    self.name = dict["name"]
                    if self.name != "":
                        self.fileName = dict["fileName"]
                        self.unkA = dict["unkA"]
                        self.zippedName = dict["zippedName"]
                else:
                    self.name = name
                    if self.name != "":
                        self.fileName = read_filename(sdat)
                        self.unkA = read_short(sdat)
                        self.zippedName = None
            def write(self, sdat):
                if self.name != "":
                    append_short(sdat, sdat.names[FILE].index(self.fileName))
                    append_short(sdat, self.unkA)
        class BANKInfo:
            def __init__(self, sdat, name, dict=None, blank=False):
                if dict:
                    self.name = dict["name"]
                    if self.name != "":
                        self.fileName = dict["fileName"]
                        self.unkA = dict["unkA"]
                        self.wa = dict["wa"]
                else:
                    self.name = name
                    if self.name != "":
                        self.fileName = read_filename(sdat)
                        self.unkA = read_short(sdat)
                        self.wa = [""] * 4
                        for i in range(4):
                            self.wa[i] = read_item_name(sdat, WAVARC)
                if blank:
                    self.name = None
                    self.fileName = None
                    self.unkA = None
                    self.wa = [""] * 4
            def write(self, sdat):
                if self.name != "":
                    append_short(sdat, sdat.names[FILE].index(self.fileName))
                    append_short(sdat, self.unkA)
                    for i in range(4):
                        if(self.wa[i] == ""):
                            append_short(sdat, 0xFFFF)
                        else:
                            append_short(sdat, [i.name for i in sdat.infoBlock.wavarcInfo].index(self.wa[i]))
        class WAVARCInfo:
            def __init__(self, sdat, name, dict=None, blank=False):
                if dict:
                    self.name = dict["name"]
                    if self.name != "":
                        self.fileName = dict["fileName"]
                        self.unkA = dict["unkA"]
                else:
                    self.name = name
                    if self.name != "":
                        self.fileName = read_filename(sdat)
                        self.unkA = read_short(sdat)
                if blank:
                    self.name = None
                    self.fileName = None
                    self.unkA = None
            def write(self, sdat):
                if self.name != "":
                    append_short(sdat, sdat.names[FILE].index(self.fileName))
                    append_short(sdat, self.unkA)
        class PLAYERInfo:
            def __init__(self, sdat, name, dict=None):
                if dict:
                    self.name = dict["name"]
                    if self.name != "":
                        self.unkA = dict["unkA"]
                        self.padding = dict["padding"]
                        self.unkB = dict["unkB"]
                else:
                    self.name = name
                    if self.name != "":
                        self.unkA = read_byte(sdat)
                        self.padding = [None] * 3
                        for i in range(3):
                            self.padding[i] = read_byte(sdat)
                        self.unkB = read_long(sdat)
            def write(self, sdat):
                if self.name != "":
                    append_byte(sdat, self.unkA)
                    for i in range(3):
                        append_byte(sdat, self.padding[i])
                    append_long(sdat, self.unkB)
        class GROUPInfo:
            def __init__(self, sdat, name, dict=None):
                class SubGROUP:
                    def __init__(self, sdat, dict=None):
                        if dict:
                            self.type = dict["type"]
                            self.entry = dict["entry"]
                        else:
                            self.type = read_long(sdat)
                            self.entry = read_long(sdat)
                if dict:
                    self.name = dict["name"]
                    if self.name != "":
                        self.count = dict["count"]
                        self.subGroup = []
                        for i in range(len(dict["subGroup"])):
                            self.subGroup.append(SubGROUP(sdat, dict=dict["subGroup"][i]))
                else:
                    self.name = name
                    if self.name != "":
                        self.count = read_long(sdat)
                        self.subGroup = [None] * self.count
                        for i in range(self.count):
                            self.subGroup[i] = SubGROUP(sdat)
            def write(self, sdat):
                if self.name != "":
                    append_long(sdat, self.count)
                    for i in range(self.count):
                        append_long(sdat, self.subGroup[i].type)
                        append_long(sdat, self.subGroup[i].entry)
        class PLAYER2Info:
            def __init__(self, sdat, name, dict=None):
                if dict:
                    self.name = dict["name"]
                    if self.name != "":
                        self.count = dict["count"]
                        self.v = dict["v"]
                        self.reserved = dict["reserved"]
                else:
                    self.name = name
                    if self.name != "":
                        self.count = read_byte(sdat)
                        self.v = [None] * 16
                        for i in range(16):
                            self.v[i] = read_byte(sdat)
                        self.reserved = [None] * 7
                        for i in range(7):
                            self.reserved[i] = read_byte(sdat)
            def write(self, sdat):
                if self.name != "":
                    append_byte(sdat, self.count)
                    for i in range(16):
                        append_byte(sdat, self.v[i])
                    for i in range(7):
                        append_byte(sdat, self.reserved[i])
        class STRMInfo:
            def __init__(self, sdat, name, dict=None):
                if dict:
                    self.name = dict["name"]
                    if self.name != "":
                        self.fileName = dict["fileName"]
                        self.unkA = dict["unkA"]
                        self.vol = dict["vol"]
                        self.pri = dict["pri"]
                        self.ply = dict["ply"]
                        self.reserved = dict["reserved"]
                else:
                    self.name = name
                    if self.name != "":
                        self.fileName = read_filename(sdat)
                        self.unkA = read_short(sdat)
                        self.vol = read_byte(sdat)
                        self.pri = read_byte(sdat)
                        self.ply = read_byte(sdat)
                        self.reserved = [None] * 5
                        for i in range(5):
                            self.reserved[i] = read_byte(sdat)
            def write(self, sdat):
                if self.name != "":
                    append_short(sdat, sdat.names[FILE].index(self.fileName))
                    append_short(sdat, self.unkA)
                    append_byte(sdat, self.vol)
                    append_byte(sdat, self.pri)
                    append_byte(sdat, self.ply)
                    for i in range(5):
                        append_byte(sdat, self.reserved[i])
        def __init__(self):
            for group in infoBlockGroup:
                exec(f"self.{group} = []")
        def load(self, sdat, infile):
            for index, group in enumerate(infoBlockGroup):
                exec(f"""for i in range(len(infile['{group}'])):
                    self.{group}.append(self.{infoBlockGroupType[index]}(sdat, None, dict=infile['{group}'][i]))""")

        def write(self, sdat, type, index=-1):
            if index == -1:
                for i in range(len(type)):
                    type[i].write(sdat)
            else:
                type[index].write(sdat)
        def replace_file(self, type, oldFile, newFile):
            exec(f"""for item in self.{infoBlockGroup[eval(type)]}:
                if item.name != "":
                    if item.fileName == oldFile:
                        item.fileName = newFile""")

    class FileBlock:
        class File:
            def __init__(self, name, type, dict=None):
                if dict:
                    self.name = dict["name"]
                    self.type = dict["type"]
                    self.MD5 = dict["MD5"]
                    if "subFile" in dict:
                        self.subFile = dict["subFile"]
                else:
                    self.name = name
                    self.type = type
                    self.MD5 = None
        def __init__(self):
            self.file = []
        def load(self, infile):
            for i in range(len(infile["file"])):
                self.file.append(self.File(None, None, dict=infile["file"][i]))

    def __init__(self, fileName=None, noSymbBlock=False):
        self.itemOffset = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.itemSymbOffset = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.itemCount = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.names = [[], [], [], [], [], [], [], [], []]
        self.fileType = []
        self.fileNameID = []

        if fileName:
            with open(fileName, "rb") as infile:
                self.data = bytearray(infile.read())
            self.fileSize = len(self.data)
            self.pos = 8
            self.SDATSize = read_long(self)
            self.headerSize = read_short(self)
            self.blocks = read_short(self)
            if self.blocks == 4:
                self.symbOffset = read_long(self)
                self.symbSize = read_long(self)
            self.infoOffset = read_long(self)
            self.infoSize = read_long(self)
            self.fatOffset = read_long(self)
            self.fatSize = read_long(self)
            self.fileOffset = read_long(self)
            self.fileSize = read_long(self)
        else:
            self.data = bytearray()
            self.pos = 0
            self.blocks = 4
            if noSymbBlock:
                self.blocks = 3
            self.data = bytearray(b'SDAT')  # Header
            self.data += b'\xFF\xFE\x00\x01'  # Magic
            self.data += bytearray(4)  # File size
            append_short(self, (self.blocks + 4) * 8)  # Header size
            append_short(self, self.blocks)  # Blocks
            self.data += bytearray((self.blocks + 2) * 8)  # reserve space for the offsets and sizes
            self.headeri = 0  # help point back to the block offsets and sizes when ready to write


def unpack_symbBlock(sdat):
    sdat.seqarcName = []
    sdat.seqarcNameID = []
    if sdat.blocks == 4:
        sdat.pos = sdat.symbOffset + 8
        for i in range(8):
            sdat.itemSymbOffset[i] = read_long(sdat, pos=sdat.pos + (i * 4)) + sdat.symbOffset
        for i in range(8):
            if i != SEQARC:
                sdat.pos = sdat.itemSymbOffset[i]
                entries = read_long(sdat, pos=sdat.pos)
                for ii in range(entries):
                    sdat.pos = read_long(sdat, pos=sdat.itemSymbOffset[i] + 4 + (ii * 4)) + sdat.symbOffset
                    sdat.names[i].append(get_string(sdat))
            else:
                sdat.pos = sdat.itemSymbOffset[i]
                entries = read_long(sdat, pos=sdat.pos)
                for ii in range(entries):
                    sdat.pos = read_long(sdat, pos=sdat.itemSymbOffset[i] + 4 + (ii * 8)) + sdat.symbOffset
                    sdat.names[i].append(get_string(sdat))
                    sdat.pos = read_long(sdat, pos=sdat.itemSymbOffset[i] + 8 + (ii * 8)) + sdat.symbOffset
                    SEQARCSubOffset = sdat.pos
                    count = read_long(sdat, pos=sdat.pos)
                    for x in range(count):
                        sdat.pos = read_long(sdat, pos=SEQARCSubOffset + 4 + (x * 4)) + sdat.symbOffset
                        if entries > 0:
                            sdat.seqarcName.append(get_string(sdat))
                            sdat.seqarcNameID.append(ii)  


def build_symbBlock(sdat):
    if sdat.blocks == 4:  # symbBlock
        sdat.symbBlockOffset = len(sdat.data)
        sdat.data += b'SYMB'  # Header
        sdat.data += bytearray(4)  # symbBlock size
        sdat.data += bytearray(8 * 4)  # reserve space for the offsets
        sdat.data += bytearray(24)  # reserved bytes

        for i in range(8):
            sdat.itemSymbOffset[i] = len(sdat.data)
            write_long(sdat, sdat.symbBlockOffset + (i * 4) + 8, sdat.itemSymbOffset[i] - sdat.symbBlockOffset)
            append_long(sdat, sdat.itemCount[i])
            if i != SEQARC:
                sdat.data += bytearray(sdat.itemCount[i] * 4)
            else:
                seqarcSymbSubOffset = []
                sdat.data += bytearray(sdat.itemCount[i] * 8)  # this has sub-groups
                for ii in range(sdat.itemCount[i]):
                    write_long(sdat, (sdat.itemSymbOffset[i] + 8) + (ii * 8), len(sdat.data) - sdat.symbBlockOffset)
                    seqarcSymbSubOffset.append(len(sdat.data))
                    append_long(sdat, sdat.seqarcSymbSubCount[ii])
                    sdat.data += bytearray(sdat.seqarcSymbSubCount[ii] * 4)

        for i in range(8):
            if i != SEQARC:
                for ii in range(sdat.itemCount[i]):
                    if sdat.names[i][ii] != "":
                        write_long(sdat, (sdat.itemSymbOffset[i] + 4) + (ii * 4), len(sdat.data) - sdat.symbBlockOffset)
                        for x, character in enumerate(sdat.names[i][ii]):
                            append_byte(sdat, ord(character))
                        append_byte(sdat, 0)  # terminate string
            else:
                for ii in range(sdat.itemCount[i]):
                    if sdat.names[i][ii] != "":
                        write_long(sdat, (sdat.itemSymbOffset[i] + 4) + (ii * 8), len(sdat.data) - sdat.symbBlockOffset)
                        for x, character in enumerate(sdat.names[i][ii]):
                            append_byte(sdat, ord(character))
                        append_byte(sdat, 0)  # terminate string
                        curSeqarcSub = 0
                        for subi, name in enumerate(sdat.seqarcSymbSubName):
                            if sdat.seqarcSymbSubParent[subi] == ii:
                                if name != "":
                                    write_long(sdat, (seqarcSymbSubOffset[ii] + 4) + (curSeqarcSub * 4), len(sdat.data) - symbBlockOffset)
                                    for x, character in enumerate(name):
                                        append_byte(sdat, ord(character))
                                    append_byte(sdat, 0)  # terminate string
                                curSeqarcSub += 1

        write_long(sdat, 16, sdat.symbBlockOffset)
        write_long(sdat, 20, len(sdat.data) - sdat.symbBlockOffset)
        sdat.headeri += 1
        sdat.data += bytearray((4 - (len(sdat.data) & 3)) & 3)  # pad to the nearest 0x04 byte alignment
        write_long(sdat, sdat.symbBlockOffset + 4, len(sdat.data) - sdat.symbBlockOffset)


def unpack_infoBlock(sdat):
    sdat.infoBlock = sdat.InfoBlock()
    sdat.pos = sdat.infoOffset + 8
    for i in range(8):
        sdat.itemOffset[i] = read_long(sdat, pos=sdat.pos + (i * 4)) + sdat.infoOffset
    for i in range(8):
        sdat.pos = sdat.itemOffset[i]
        entries = read_long(sdat, pos=sdat.pos)
        for ii in range(entries):
            sdat.pos = read_long(sdat, pos=sdat.itemOffset[i] + 4 + (ii * 4)) + sdat.infoOffset
            if sdat.pos - sdat.infoOffset > 0x40:
                count = read_long(sdat, pos=sdat.pos)  # count is only used for group
                if sdat.blocks == 4 and ii < len(sdat.names[i]):
                    iName = sdat.names[i][ii]
                else:
                    iName = f"{itemString[i]}_{ii}"
                if i in (SEQ, SEQARC, BANK, WAVARC, STRM):  # These have files
                    sdat.fileType.append(i)
                    sdat.fileNameID.append(read_short(sdat, pos=sdat.pos))
                    sdat.names[FILE].append(iName)
            else:
                iName = ""
            exec(f"sdat.infoBlock.{infoBlockGroup[i]}.append(sdat.infoBlock.{infoBlockGroupType[i]}(sdat, iName))")
            if i == SEQARC:
                sdat.infoBlock.seqarcInfo[-1].zippedName = [sdat.seqarcName[id] for id, num in enumerate(sdat.seqarcNameID) if num == ii]


def build_infoBlock(sdat):
    sdat.infoBlockOffset = len(sdat.data)  # infoBlock
    sdat.data += b'INFO'  # Header
    sdat.data += bytearray(4)  # File size
    sdat.data += bytearray(8 * 4)  # reserve space for the offsets
    sdat.data += bytearray(24)  # reserved bytes

    for i in range(8):
        sdat.itemOffset[i] = len(sdat.data)
        write_long(sdat, sdat.infoBlockOffset + (i * 4) + 8, sdat.itemOffset[i] - sdat.infoBlockOffset)
        append_long(sdat, sdat.itemCount[i])
        sdat.data += bytearray(sdat.itemCount[i] * 4)
        for ii in range(sdat.itemCount[i]):
            write_long(sdat, (sdat.itemOffset[i] + 4) + (ii * 4), len(sdat.data) - sdat.infoBlockOffset)
            tempSize = len(sdat.data)
            exec(f"sdat.infoBlock.write(sdat, sdat.infoBlock.{infoBlockGroup[i]}, ii)")
            if tempSize == len(sdat.data):  # Null out the pointer for null items
                write_long(sdat, (sdat.itemOffset[i] + 4) + (ii * 4), 0)

    write_long(sdat, 16 + (sdat.headeri * 8), sdat.infoBlockOffset)
    write_long(sdat, 20 + (sdat.headeri * 8), len(sdat.data) - sdat.infoBlockOffset)
    sdat.headeri += 1
    sdat.data += bytearray((4 - (len(sdat.data) & 3)) & 3)  # pad to the nearest 0x04 byte alignment
    write_long(sdat, sdat.infoBlockOffset + 4, len(sdat.data) - sdat.infoBlockOffset)


def build_fatBlock(sdat):
    sdat.fatBlockOffset = len(sdat.data)  # fatBlock
    sdat.data += b'FAT\x20'  # Header
    append_long(sdat, (sdat.itemCount[FILE] * 16) + 12)  # fatBlock size
    append_long(sdat, sdat.itemCount[FILE])  # number of FAT records
    sdat.data += bytearray((sdat.itemCount[FILE] * 16))

    write_long(sdat, 16 + (sdat.headeri * 8), sdat.fatBlockOffset)
    write_long(sdat, 20 + (sdat.headeri * 8), len(sdat.data) - sdat.fatBlockOffset)
    sdat.headeri += 1
    sdat.data += bytearray((4 - (len(sdat.data) & 3)) & 3)  # pad to the nearest 0x04 byte alignment
    write_long(sdat, sdat.fatBlockOffset + 4, len(sdat.data) - sdat.fatBlockOffset)


def unpack_fileBlock(sdat, args):
    sdat.fileBlock = sdat.FileBlock()
    sdat.pos = sdat.fatOffset + 8
    entries = read_long(sdat, pos=sdat.pos)
    if not os.path.exists(f"{args.folder}/Files"):
        os.makedirs(f"{args.folder}/Files")
    if not os.path.exists(f"{args.folder}/Files/{itemString[SEQ]}"):
        os.makedirs(f"{args.folder}/Files/{itemString[SEQ]}")
    if not os.path.exists(f"{args.folder}/Files/{itemString[SEQARC]}"):
        os.makedirs(f"{args.folder}/Files/{itemString[SEQARC]}")
    if not os.path.exists(f"{args.folder}/Files/{itemString[BANK]}"):
        os.makedirs(f"{args.folder}/Files/{itemString[BANK]}")
    if not os.path.exists(f"{args.folder}/Files/{itemString[WAVARC]}"):
        os.makedirs(f"{args.folder}/Files/{itemString[WAVARC]}")
    if not os.path.exists(f"{args.folder}/Files/{itemString[STRM]}"):
        os.makedirs(f"{args.folder}/Files/{itemString[STRM]}")
    for i in range(entries):
        sdat.pos = read_long(sdat, pos=sdat.fatOffset + 12 + (i * 16))
        tempSize = read_long(sdat, pos=sdat.fatOffset + 16 + (i * 16))
        done = False
        fileRefID = 0
        fileHeader = sdat.data[sdat.pos:(sdat.pos + 4)]
        if fileHeader in itemHeader:
            tempPath = f"{args.folder}/Files/{itemString[itemHeader.index(fileHeader)]}/unknown_{i:02}"
            tempName = f"unknown_{i:02}"
            tempExt = itemExt[itemHeader.index(fileHeader)]
            tempType = itemString[itemHeader.index(fileHeader)]
        else:
            tempPath = f"{args.folder}/Files/unknown_{i:02}"
            tempName = f"unknown_{i:02}"
            tempExt = ""
            tempType = ""
        while sdat.fileNameID[fileRefID] != i and not done:
            fileRefID += 1
            if fileRefID >= len(sdat.fileNameID):
                fileRefID = -1
                done = True
        if fileRefID != -1:
            tempPath = f"{args.folder}/Files/{itemString[sdat.fileType[fileRefID]]}/{sdat.names[FILE][fileRefID]}"
            tempName = sdat.names[FILE][fileRefID]
        sdat.fileBlock.file.append(sdat.fileBlock.File(f"{tempName}{tempExt}", tempType))
        if fileHeader == b'SWAR':
            numSwav = read_long(sdat, pos=sdat.pos + 0x38)
            sdat.fileBlock.file[-1].subFile = []
            if not os.path.exists(tempPath):
                os.makedirs(tempPath)
            for ii in range(numSwav):
                sdat.fileBlock.file[-1].subFile.append(f"{hex(ii).lstrip('0x').rstrip('L').zfill(2).upper()}.swav")
                swavOffset = sdat.pos + read_long(sdat, pos=sdat.pos + (ii * 4) + 0x3C)
                swavLength = sdat.pos + read_long(sdat, pos=sdat.pos + ((ii + 1) * 4) + 0x3C)
                if ii + 1 == numSwav:
                    swavLength = sdat.pos + tempSize
                swavSize = swavLength - swavOffset
                with open(f"{tempPath}/{hex(ii).lstrip('0x').rstrip('L').zfill(2).upper()}.swav", "wb") as outfile:
                    outfile.write(b'SWAV')  # Header
                    outfile.write(b'\xFF\xFE\x00\x01')  # magic
                    outfile.write((swavSize + 0x18).to_bytes(4, byteorder='little'))
                    outfile.write(b'\x10\x00\x01\x00')  # structure size and blocks
                    outfile.write(b'DATA')
                    outfile.write((swavSize + 0x08).to_bytes(4, byteorder='little'))
                    outfile.write(sdat.data[swavOffset:swavLength])
        elif fileHeader == b'SBNK':
            numInst = read_long(sdat, pos=sdat.pos + 0x38)
            sbnkEnd = read_long(sdat, pos=sdat.pos + 0x08) + sdat.pos
            with open(f"{tempPath}.txt", "w") as sbnkIDFile:
                instType = []
                instOffset = []
                instOrder = []
                instUsed = []
                lastPointer = -1  # Because some instruments will point to the same exact definition
                furthestRead = sdat.pos + 0x3C + (numInst * 4)  # Because someone decided to leave in data that's not pointed to...
                for ii in range(numInst):
                    instType.append(sdat.data[sdat.pos + 0x3C + (ii * 4)])
                    instOffset.append(read_short(sdat, pos=sdat.pos + 0x3C + (ii * 4) + 1))
                    instOrder.append(-1)
                    instUsed.append(False)
                for ii in range(numInst):  # get the order the data is stored for 1:1 builds
                    lowestPointer = 0xFFFFFFFF
                    lowestPointerID = -1
                    for x in range(numInst):
                        if not instUsed[x]:
                            if lowestPointer > instOffset[x]:
                                lowestPointer = instOffset[x]
                                lowestPointerID = x
                    instOrder[ii] = lowestPointerID
                    instUsed[lowestPointerID] = True
                for ii in range(numInst):
                    if instOffset[instOrder[ii]] == lastPointer and lastPointer > 0:
                        sbnkIDFile.write(str(instOrder[ii]))
                        sbnkIDFile.write(", SameAsAbove\n")
                    elif instType[instOrder[ii]] == 0:
                        sbnkIDFile.write(str(instOrder[ii]))
                        sbnkIDFile.write(", NULL\n")
                    elif instType[instOrder[ii]] < 16:
                        if furthestRead < sdat.pos + instOffset[instOrder[ii]]:
                            sbnkIDFile.write("Unused")
                            while furthestRead < sdat.pos + instOffset[instOrder[ii]]:
                                sbnkIDFile.write(f", {sdat.data[furthestRead]}")
                                furthestRead += 1
                            sbnkIDFile.write("\n")
                        sbnkIDFile.write(str(instOrder[ii]))
                        if instType[instOrder[ii]] == 1:
                            sbnkIDFile.write(", Single")
                        elif instType[instOrder[ii]] == 2:
                            sbnkIDFile.write(", PSG1")
                        elif instType[instOrder[ii]] == 3:
                            sbnkIDFile.write(", PSG2")
                        elif instType[instOrder[ii]] == 4:
                            sbnkIDFile.write(", PSG3")
                        else:
                            sbnkIDFile.write(f", {instType[instOrder[ii]]}")
                        sbnkIDFile.write(f", {read_short(sdat, pos=sdat.pos + instOffset[instOrder[ii]])}")
                        sbnkIDFile.write(f", {read_short(sdat, pos=sdat.pos + instOffset[instOrder[ii]] + 2)}")
                        sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 4]}")
                        sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 5]}")
                        sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 6]}")
                        sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 7]}")
                        sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 8]}")
                        sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 9]}\n")
                        if sdat.pos + instOffset[instOrder[ii]] + 9 > furthestRead:
                            furthestRead = sdat.pos + instOffset[instOrder[ii]] + 10
                    elif instType[instOrder[ii]] == 16:
                        if furthestRead < sdat.pos + instOffset[instOrder[ii]]:
                            sbnkIDFile.write("Unused")
                            while furthestRead < sdat.pos + instOffset[instOrder[ii]]:
                                sbnkIDFile.write(f", {sdat.data[furthestRead]}")
                                furthestRead += 1
                            sbnkIDFile.write("\n")
                        sbnkIDFile.write(str(instOrder[ii]))
                        lowNote = sdat.data[sdat.pos + instOffset[instOrder[ii]]]
                        highNote = sdat.data[sdat.pos + instOffset[instOrder[ii]] + 1]
                        sbnkIDFile.write(f", Drums, {lowNote}, {highNote}\n")
                        x = 0
                        while read_short(sdat, pos=sdat.pos + instOffset[instOrder[ii]] + 2 + (x * 12)) == 1 and read_short(sdat, pos=sdat.pos + instOffset[instOrder[ii]] + 6 + (x * 12)) < 4:
                            sbnkIDFile.write(f"\t{read_short(sdat, pos=sdat.pos + instOffset[instOrder[ii]] + 2 + (x * 12))}")
                            sbnkIDFile.write(f", {read_short(sdat, pos=sdat.pos + instOffset[instOrder[ii]] + 4 + (x * 12))}")
                            sbnkIDFile.write(f", {read_short(sdat, pos=sdat.pos + instOffset[instOrder[ii]] + 6 + (x * 12))}")
                            sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 8 + (x * 12)]}")
                            sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 9 + (x * 12)]}")
                            sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 10 + (x * 12)]}")
                            sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 11 + (x * 12)]}")
                            sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 12 + (x * 12)]}")
                            sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 13 + (x * 12)]}\n")
                            x += 1
                        x -= 1
                        if sdat.pos + instOffset[instOrder[ii]] + 13 + (x * 12) > furthestRead:
                            furthestRead = sdat.pos + instOffset[instOrder[ii]] + 14 + (x * 12)
                    elif instType[instOrder[ii]] == 17:
                        if furthestRead < sdat.pos + instOffset[instOrder[ii]]:
                            sbnkIDFile.write("Unused")
                            while furthestRead < sdat.pos + instOffset[instOrder[ii]]:
                                sbnkIDFile.write(f", {sdat.data[furthestRead]}")
                                furthestRead += 1
                            sbnkIDFile.write("\n")
                        sbnkIDFile.write(str(instOrder[ii]))
                        regions = 0
                        sbnkIDFile.write(", Keysplit")
                        for x in range(8):
                            if sdat.data[sdat.pos + instOffset[instOrder[ii]] + x] > 0:
                                regions += 1
                            sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + x]}")
                        sbnkIDFile.write("\n")
                        tempOffset = sdat.pos + instOffset[instOrder[ii]] + 8
                        for x in range(regions):
                            sbnkIDFile.write(f"\t{read_short(sdat, pos=sdat.pos + instOffset[instOrder[ii]] + 8 + (x * 12))}")
                            sbnkIDFile.write(f", {read_short(sdat, pos=sdat.pos + instOffset[instOrder[ii]] + 10 + (x * 12))}")
                            sbnkIDFile.write(f", {read_short(sdat, pos=sdat.pos + instOffset[instOrder[ii]] + 12 + (x * 12))}")
                            sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 14 + (x * 12)]}")
                            sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 15 + (x * 12)]}")
                            sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 16 + (x * 12)]}")
                            sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 17 + (x * 12)]}")
                            sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 18 + (x * 12)]}")
                            sbnkIDFile.write(f", {sdat.data[sdat.pos + instOffset[instOrder[ii]] + 19 + (x * 12)]}\n")
                            if sdat.pos + instOffset[instOrder[ii]] + 19 + (x * 12) > furthestRead:
                                furthestRead = sdat.pos + instOffset[instOrder[ii]] + 20 + (x * 12)
                    lastPointer = instOffset[instOrder[ii]]
                if furthestRead < sbnkEnd:
                    sbnkIDFile.write("Unused")
                    while furthestRead < sbnkEnd:
                        sbnkIDFile.write(f", {sdat.data[furthestRead]}")
                        furthestRead += 1
                    sbnkIDFile.write("\n")
        elif fileHeader == b'SSEQ':
            sseqSize = read_long(sdat, pos=sdat.pos + 0x14)
            sseqEnd = sdat.pos + 16 + sseqSize
            sdat.pos += 0x1C
            sseqStart = sdat.pos

            # Run through first to calculate labels
            trackOffset = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            trackLabel = []
            trackLabelName = []
            command = sdat.data[sdat.pos]
            if command == 0xFE:
                usedTracks = read_short(sdat, pos=sdat.pos + 1)
                sdat.pos += 3
                numTracks = 0
                curTrack = 1
                while curTrack < 16:
                    if usedTracks & curTrack:
                        numTracks += 1
                    curTrack <<= 1
            else:
                sdat.pos = sseqEnd

            trackOffset[0] = sdat.pos  # Workaround to place the first track header
            while sdat.pos < sseqEnd:
                command = sdat.data[sdat.pos]
                sdat.pos += 1  # temporary
                if command == 0x93:  # Track Pointer
                    trackInfo = read_long(sdat, pos=sdat.pos)
                    trackOffset[trackInfo & 0xFF] = (trackInfo >> 8) + sseqStart
                    sdat.pos += 4
                elif (command == 0x94) or (command == 0x95):  # Jump or Call
                    commandArgLen = sseqCmdArgs[command - 0x80]
                    commandArg = (read_long(sdat, pos=sdat.pos) & 0xFFFFFF) + sseqStart
                    if commandArg not in trackLabel:
                        trackLabel.append(commandArg)
                        if commandArg not in trackOffset:
                            trackLabelName.append(f"Label_0x{hex(commandArg).lstrip('0x').rstrip('L').zfill(2).upper()}")
                        else:
                            trackLabelName.append(f"Track_{trackOffset.index(commandArg) + 1}")
                    sdat.pos += commandArgLen
                elif command >= 0x80:
                    commandArgLen = sseqCmdArgs[command - 0x80]
                    if commandArgLen == -1:
                        for i in range(3):
                            if sdat.data[sdat.pos] > 0x7F:
                                sdat.pos += 1
                        sdat.pos += 1
                    else:
                        sdat.pos += commandArgLen
                else:
                    sdat.pos += 1
                    for i in range(3):
                        if sdat.data[sdat.pos] > 0x7F:
                            sdat.pos += 1
                    sdat.pos += 1

            # Re-run through the song now that the labels are defined
            sdat.pos = sseqStart
            with open(f"{tempPath}.txt", "w") as sseqFile:
                command = sdat.data[sdat.pos]
                if command == 0xFE:
                    usedTracks = read_short(sdat, pos=sdat.pos + 1)
                    sdat.pos += 3
                    numTracks = 0
                    curTrack = 1
                    while curTrack < 16:
                        if usedTracks & curTrack:
                            numTracks += 1
                        curTrack <<= 1
                else:
                    sdat.pos = sseqEnd

                curTrack = 0
                trackOffset[0] = sdat.pos  # Workaround to place the first track header
                while sdat.pos < sseqEnd:
                    if sdat.pos in trackOffset:
                        sseqFile.write(f"Track_{trackOffset.index(sdat.pos) + 1}:\n")
                    elif sdat.pos in trackLabel:
                        sseqFile.write(f"{trackLabelName[trackLabel.index(sdat.pos)]}:\n")
                    command = sdat.data[sdat.pos]
                    sdat.pos += 1  # temporary
                    if command == 0x93:  # Track Pointer
                        trackInfo = read_long(sdat, pos=sdat.pos)
                        trackOffset[trackInfo & 0xFF] = (trackInfo >> 8) + sseqStart
                        sdat.pos += 4
                    elif command >= 0x80:
                        commandName = sseqCmdName[command - 0x80]
                        if commandName == "":
                            commandName = f"Unknown_0x{hex(command).lstrip('0x').rstrip('L').zfill(2).upper()}"
                        commandArgLen = sseqCmdArgs[command - 0x80]
                        if commandArgLen == -1:
                            commandArgLen = 1
                            commandArg = (sdat.data[sdat.pos] & 0x7F)
                            for i in range(3):
                                if sdat.data[sdat.pos] > 0x7F:
                                    commandArg <<= 7
                                    commandArg += (sdat.data[sdat.pos] & 0x7F)
                                    sdat.pos += 1
                                    commandArgLen += 1
                            sdat.pos += 1
                        else:
                            commandArgMask = 0
                            for i in range(commandArgLen):
                                commandArgMask <<= 8
                                commandArgMask += 0xFF
                            commandArg = (read_long(sdat, pos=sdat.pos) & commandArgMask)
                            sdat.pos += commandArgLen
                        if commandArgLen != 0:
                            if (command == 0x94) or (command == 0x95):  # Jump or Call
                                sseqFile.write(f"\t{commandName} {trackLabelName[trackLabel.index(commandArg + sseqStart)]}\n")
                            else:
                                sseqFile.write(f"\t{commandName} {commandArg}\n")
                        else:
                            sseqFile.write(f"\t{commandName}\n")
                    else:
                        velocity = sdat.data[sdat.pos]
                        sdat.pos += 1
                        commandArg = (sdat.data[sdat.pos] & 0x7F)
                        commandArgLen = 1
                        for i in range(3):
                            if sdat.data[sdat.pos] > 0x7F:
                                commandArg <<= 7
                                commandArg += (sdat.data[sdat.pos] & 0x7F)
                                sdat.pos += 1
                                commandArgLen += 1
                        sdat.pos += 1
                        sseqFile.write(f"\t{sseqNote[command % 12]}{int(command / 12)},{velocity},{commandArg}\n")
            sdat.pos = sseqStart - 0x1C
        with open(tempPath + tempExt, "wb") as outfile:
            outfile.write(sdat.data[sdat.pos:(sdat.pos + tempSize)])
        tempFileString = sdat.data[sdat.pos:(sdat.pos + tempSize)]
        thisMD5 = hashlib.md5(tempFileString)
        sdat.fileBlock.file[-1].MD5 = f"{thisMD5.hexdigest()}"


def build_fileBlock(sdat, args):
    sdat.fileBlockOffset = len(sdat.data)  # fileBlock
    sdat.data += b'FILE'  # Header
    sdat.data += bytearray(4)  # fileBlock size
    append_long(sdat, sdat.itemCount[FILE])  # number of files
    sdat.data += bytearray(4)  # reserved
    sdat.data += bytearray((0x20 - (len(sdat.data) & 0x1F)) & 0x1F)  # pad to the nearest 0x20 byte alignment

    for i, fName in enumerate(sdat.names[FILE]):  # Check for BANK source files
        testPath = f"{args.folder}/Files/{itemString[itemExt.index(fName[-5:])]}/{fName}"
        if not os.path.exists(testPath):
            if fName[-5:] == ".sbnk":  # can the sbnk be built?
                testPath = f"{args.folder}/Files/{itemString[BANK]}/{fName[:-5]}.txt"
                if not os.path.exists(testPath):
                    raise Exception(f"Missing File:{testPath}")
                with open(testPath, "r") as sbnkIDFile:
                    done = False
                    sbnkLines = []
                    numInst = 0
                    while not done:
                        thisLine = sbnkIDFile.readline()
                        if not thisLine:
                            done = True
                        thisLine = thisLine.split(";")[0]  # ignore anything commented out
                        thisLine = thisLine.split("\n")[0]  # remove newline
                        if thisLine != "":
                            sbnkLines.append(thisLine)
                            if thisLine.find("\t") == -1 and thisLine.find("Unused") == -1:  # Don't count unused or sub definitions
                                numInst += 1
                sbnkHeader = []
                sbnkHeaderSize = 0x3C
                sbnkData = []
                prevPointer = b'\x00\x00\x00\x00'
                sbnkHeader.append(b'SBNK')  # Header
                sbnkHeader.append(b'\xFF\xFE\x00\x01')  # magic
                sbnkHeader.append(b'\x00\x00\x00\x00')  # Reserve for sbnk size
                sbnkHeader.append(b'\x10\x00\x01\x00')  # structure size and blocks
                sbnkHeader.append(b'DATA')
                sbnkHeader.append(b'\x00\x00\x00\x00')  # Reserve for struct size
                sbnkHeader.append(b'\x00' * 32)  # reserved
                sbnkHeader.append((numInst).to_bytes(4, byteorder='little'))  # Number of instruments
                for ii in range(numInst):
                    sbnkHeader.append(b'\x00\x00\x00\x00')  # Reserve for pointers
                for ii, inst in enumerate(sbnkLines):
                    thisLine = inst
                    if thisLine.find("\t") == -1:
                        thisLine = thisLine.split(", ")
                        if thisLine[1] == "SameAsAbove":
                            sbnkHeader[8 + int(thisLine[0])] = prevPointer
                        elif thisLine[1] != "0" and thisLine[1] != "NULL":
                            if thisLine[1] == "Single":
                                thisLine[1] = "1"
                            elif thisLine[1] == "PSG1":
                                thisLine[1] = "2"
                            elif thisLine[1] == "PSG2":
                                thisLine[1] = "3"
                            elif thisLine[1] == "PSG3":
                                thisLine[1] = "4"
                            elif thisLine[1] == "Drums":
                                thisLine[1] = "16"
                            elif thisLine[1] == "Keysplit":
                                thisLine[1] = "17"
                            sbnkHeaderSize = (numInst * 4) + 0x3C
                            if thisLine[0] == "Unused":
                                for x, unusedData in enumerate(thisLine[1:]):
                                    sbnkData.append((int(unusedData)).to_bytes(1, byteorder='little'))
                            else:
                                prevPointer = (int(thisLine[1]) + ((sbnkHeaderSize + sum(len(tf) for tf in sbnkData)) << 8)).to_bytes(4, byteorder='little')
                                sbnkHeader[8 + int(thisLine[0])] = prevPointer
                            if int(thisLine[1]) < 16:
                                sbnkData.append((int(thisLine[2])).to_bytes(2, byteorder='little'))
                                sbnkData.append((int(thisLine[3])).to_bytes(2, byteorder='little'))
                                sbnkData.append((int(thisLine[4])).to_bytes(1, byteorder='little'))
                                sbnkData.append((int(thisLine[5])).to_bytes(1, byteorder='little'))
                                sbnkData.append((int(thisLine[6])).to_bytes(1, byteorder='little'))
                                sbnkData.append((int(thisLine[7])).to_bytes(1, byteorder='little'))
                                sbnkData.append((int(thisLine[8])).to_bytes(1, byteorder='little'))
                                sbnkData.append((int(thisLine[9])).to_bytes(1, byteorder='little'))
                            elif int(thisLine[1]) == 16:
                                sbnkData.append((int(thisLine[2])).to_bytes(1, byteorder='little'))
                                sbnkData.append((int(thisLine[3])).to_bytes(1, byteorder='little'))
                            elif int(thisLine[1]) == 17:
                                sbnkData.append((int(thisLine[2])).to_bytes(1, byteorder='little'))
                                sbnkData.append((int(thisLine[3])).to_bytes(1, byteorder='little'))
                                sbnkData.append((int(thisLine[4])).to_bytes(1, byteorder='little'))
                                sbnkData.append((int(thisLine[5])).to_bytes(1, byteorder='little'))
                                sbnkData.append((int(thisLine[6])).to_bytes(1, byteorder='little'))
                                sbnkData.append((int(thisLine[7])).to_bytes(1, byteorder='little'))
                                sbnkData.append((int(thisLine[8])).to_bytes(1, byteorder='little'))
                                sbnkData.append((int(thisLine[9])).to_bytes(1, byteorder='little'))
                    else:
                        thisLine = thisLine.split("\t")
                        thisLine = thisLine[1]
                        thisLine = thisLine.split(", ")
                        sbnkData.append((int(thisLine[0])).to_bytes(2, byteorder='little'))
                        sbnkData.append((int(thisLine[1])).to_bytes(2, byteorder='little'))
                        sbnkData.append((int(thisLine[2])).to_bytes(2, byteorder='little'))
                        sbnkData.append((int(thisLine[3])).to_bytes(1, byteorder='little'))
                        sbnkData.append((int(thisLine[4])).to_bytes(1, byteorder='little'))
                        sbnkData.append((int(thisLine[5])).to_bytes(1, byteorder='little'))
                        sbnkData.append((int(thisLine[6])).to_bytes(1, byteorder='little'))
                        sbnkData.append((int(thisLine[7])).to_bytes(1, byteorder='little'))
                        sbnkData.append((int(thisLine[8])).to_bytes(1, byteorder='little'))
                sbnkSize = sum(len(tf) for tf in sbnkData) + sbnkHeaderSize
                while (sbnkSize & 0xFFFFFFFC) != sbnkSize:
                    sbnkData.append(b'\x00')  # pad to the nearest 0x4 byte alignment
                    sbnkSize += 1
                sbnkHeader[2] = (sbnkSize).to_bytes(4, byteorder='little')
                sbnkHeader[5] = (sbnkSize - 0x10).to_bytes(4, byteorder='little')
                testPath = f"{args.folder}/Files/{itemString[BANK]}/{fName}"
                with open(testPath, "wb") as sbnkFile:
                    for ii, listItem in enumerate(sbnkHeader):
                        sbnkFile.write(listItem)
                    for ii, listItem in enumerate(sbnkData):
                        sbnkFile.write(listItem)

    for i, fName in enumerate(sdat.names[FILE]):  # Check for WAVEARC source files
        testPath = f"{args.folder}/Files/{itemString[itemExt.index(fName[-5:])]}/{fName}"
        if not os.path.exists(testPath):
            if fName[-5:] == ".swar":  # can the swar be built?
                swavName = sdat.fileBlock.file[i].subFile
                swarTemp = []
                for ii, sName in enumerate(swavName):
                    testPath = f"{args.folder}/Files/{itemString[WAVARC]}/{fName[:-5]}/{sName}"
                    if not os.path.exists(testPath):
                        raise Exception(f"Missing File:{testPath}")
                    with open(testPath, "rb") as tempFile:
                        swarTemp.append(bytearray(tempFile.read()))
                testPath = f"{args.folder}/Files/{itemString[WAVARC]}/{fName}"
                with open(testPath, "wb") as swarFile:
                    swarSize = sum(len(sf[0x18:]) for sf in swarTemp)
                    swarFile.write(b'SWAR')  # Header
                    swarFile.write(b'\xFF\xFE\x00\x01')  # magic
                    swarFile.write((swarSize + 0x3C + (len(swarTemp) * 4)).to_bytes(4, byteorder='little'))
                    swarFile.write(b'\x10\x00\x01\x00')  # structure size and blocks
                    swarFile.write(b'DATA')
                    swarFile.write((swarSize + 0x2C + (len(swarTemp) * 4)).to_bytes(4, byteorder='little'))
                    swarFile.write(b'\x00' * 32)  # reserved
                    swarFile.write((len(swarTemp)).to_bytes(4, byteorder='little'))
                    swarPointer = 0x3C + (len(swarTemp) * 4)  # where the first swav will be in the file
                    for ii, sFile in enumerate(swarTemp):
                        swarFile.write((swarPointer).to_bytes(4, byteorder='little'))
                        swarPointer += len(sFile[0x18:])
                    for ii, sFile in enumerate(swarTemp):
                        swarFile.write(sFile[0x18:])
