from util import read_long, read_short
from Sdat import InfoBlock

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


sseqNote = (
    "C_",
    "C#",
    "D_",
    "D#",
    "E_",
    "F_",
    "F#",
    "G_",
    "G#",
    "A_",
    "A#",
    "B_",
)

sseqCmdName = (
    "Delay",  # 0x80
    "Instrument",  # 0x81
    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    "",
    "Pointer",  # 0x93
    "Jump",  # 0x94
    "Call",  # 0x95
    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    "", "", "", "", "", "", "", "", "", "",
    "Pan",  # 0xC0
    "Volume",  # 0xC1
    "MasterVolume",  # 0xC2
    "Transpose",  # 0xC3
    "PitchBend",  # 0xC4
    "PitchBendRange",  # 0xC5
    "Priority",  # 0xC6
    "Poly",  # 0xC7
    "Tie",  # 0xC8
    "PortamentoControll",  # 0xC9
    "ModDepth",  # 0xCA
    "ModSpeed",  # 0xCB
    "ModType",  # 0xCC
    "ModRange",  # 0xCD
    "PortamentoOnOff",  # 0xCE
    "PortamentoTime",  # 0xCF
    "Attack",  # 0xD0
    "Decay",  # 0xD1
    "Sustain",  # 0xD2
    "Release",  # 0xD3
    "LoopStart",  # 0xD4
    "Expression",  # 0xD5
    "Print",  # 0xD6
    "", "", "", "", "", "", "", "", "",
    "ModDelay",  # 0xE0
    "Tempo",  # 0xE1
    "",
    "PitchSweep",  # 0xE3
    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    "", "", "", "", "", "", "", "",
    "LoopEnd",  # 0xFC
    "Return\n",  # 0xFD
    "TracksUsed",  # 0xFE
    "TrackEnd\n"  # 0xFF
)

sseqCmdArgs = (  # -1 for variable length
    -1,  # 0x80
    -1,  # 0x81
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0,
    4,  # 0x93
    3,  # 0x94
    3,  # 0x95
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    1,  # 0xC0
    1,  # 0xC1
    1,  # 0xC2
    1,  # 0xC3
    1,  # 0xC4
    1,  # 0xC5
    1,  # 0xC6
    1,  # 0xC7
    1,  # 0xC8
    1,  # 0xC9
    1,  # 0xCA
    1,  # 0xCB
    1,  # 0xCC
    1,  # 0xCD
    1,  # 0xCE
    1,  # 0xCF
    1,  # 0xD0
    1,  # 0xD1
    1,  # 0xD2
    1,  # 0xD3
    1,  # 0xD4
    1,  # 0xD5
    1,  # 0xD6
    0, 0, 0, 0, 0, 0, 0, 0, 0,
    2,  # 0xE0
    2,  # 0xE1
    0,
    2,  # 0xE3
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0,  # 0xFC
    0,  # 0xFD
    2,  # 0xFE
    0  # 0xFF
)


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


def unpack_sseq(sdat, tempPath):
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