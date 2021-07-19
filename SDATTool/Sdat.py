import os
import hashlib
from const import itemHeader, itemExt, itemString, infoBlockGroup, infoBlockGroupType
from Sseq import read_sseq, write_sseq_to_txt, read_sseq_from_txt, write_sseq
from Midi import write_sseq_to_midi, read_sseq_from_midi
from Swar import unpack_swar, build_swar
from Sbnk import unpack_sbnk, build_sbnk
from const import infoBlockGroup, infoBlockGroupType, itemString
from util import read_long, read_short, read_byte, read_item_name, read_filename, \
                 append_long, append_short, append_byte, \
                 write_long, get_string

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


class InfoBlock(SDAT):
    def __init__(self):
        for group in infoBlockGroup:
            exec(f"self.{group} = []")

    def load(self, sdat, infile):
        for index, group in enumerate(infoBlockGroup):
            exec(f"""for i in range(len(infile['{group}'])):
                self.{group}.append({infoBlockGroupType[index]}(sdat, None, dict=infile['{group}'][i]))""")

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


class SEQInfo(InfoBlock):
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


class SEQARCInfo(InfoBlock):
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


class BANKInfo(InfoBlock):
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


class WAVARCInfo(InfoBlock):
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


class PLAYERInfo(InfoBlock):
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


class GROUPInfo(InfoBlock):
    class SubGROUP:
        def __init__(self, sdat, dict=None):
            if dict:
                self.type = dict["type"]
                self.entry = dict["entry"]
            else:
                self.type = read_long(sdat)
                self.entry = read_long(sdat)

    def __init__(self, sdat, name, dict=None):
        if dict:
            self.name = dict["name"]
            if self.name != "":
                self.count = dict["count"]
                self.subGroup = []
                for i in range(len(dict["subGroup"])):
                    self.subGroup.append(self.SubGROUP(sdat, dict=dict["subGroup"][i]))
        else:
            self.name = name
            if self.name != "":
                self.count = read_long(sdat)
                self.subGroup = [None] * self.count
                for i in range(self.count):
                    self.subGroup[i] = self.SubGROUP(sdat)

    def write(self, sdat):
        if self.name != "":
            append_long(sdat, self.count)
            for i in range(self.count):
                append_long(sdat, self.subGroup[i].type)
                append_long(sdat, self.subGroup[i].entry)


class PLAYER2Info(InfoBlock):
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


class STRMInfo(InfoBlock):
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
                

class FileBlock(SDAT):
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
    sdat.infoBlock = InfoBlock()
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
            exec(f"sdat.infoBlock.{infoBlockGroup[i]}.append({infoBlockGroupType[i]}(sdat, iName))")
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
    sdat.fileBlock = FileBlock()
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
            unpack_swar(sdat, tempPath)
        elif fileHeader == b'SBNK':
            unpack_sbnk(sdat, tempPath)
        elif fileHeader == b'SSEQ':
            write_sseq_to_midi(read_sseq(sdat), args, tempName)
        if args.writeRaw or (fileHeader not in [b'SWAR', b'SBNK', b'SSEQ']):
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
    sdat.data += bytearray((0x20 - (len(sdat.data) & 0x1F)) & 0x1F)  # pad to the nearest 0x20 byte alignment

    for i, fName in enumerate(sdat.names[FILE]):  # Check for source files
        testPath = f"{args.folder}/Files/{itemString[itemExt.index(fName[-5:])]}/{fName}"
        if not os.path.exists(testPath):
            if fName[-5:] == ".sbnk":  # can the sbnk be built?
                build_sbnk(sdat, args, fName)
            elif fName[-5:] == ".swar":  # can the swar be built?
                swavName = sdat.fileBlock.file[i].subFile
                build_swar(sdat, args, fName, swavName)
            elif fName[-5:] == ".sseq":  # can the sseq be built?
                write_sseq(read_sseq_from_midi(args, fName), args, fName)
