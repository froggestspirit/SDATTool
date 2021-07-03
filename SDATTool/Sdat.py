from const import infoBlockGroup, infoBlockGroupType, itemExt
from util import read_long, read_short, read_byte, read_item_name, append_long, append_short, append_byte

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


def read_filename(sdat):
    tempID = read_short(sdat)
    matchID = 0
    done = False
    while matchID < len(sdat.fileNameID) and not done:
        if sdat.fileNameID[matchID] == tempID:
            done = True
        else:
            matchID += 1
    return sdat.names[FILE][matchID] + itemExt[sdat.fileType[matchID]]


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

    def __init__(self):
        self.data = bytearray()
        self.pos = 0
        self.itemOffset = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.itemSymbOffset = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.itemCount = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.names = [[], [], [], [], [], [], [], [], []]
        self.fileType = []
        self.fileNameID = []
