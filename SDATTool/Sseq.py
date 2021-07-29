import os
from const import itemString
from util import read_long, read_short

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


seqNote = (
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
    "", "", "", "", "", "", "", "", "", "",
    "Random",  # 0xA0
    "Var",  # 0xA1
    "If",  # 0xA2
    "", "", "",
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
    "PortamentoControl",  # 0xC9
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
    "Return",  # 0xFD
    "TracksUsed",  # 0xFE
    "TrackEnd"  # 0xFF
)

sseqCmdArgs = (  # -1 for variable length
    -1,  # 0x80
    -1,  # 0x81
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0,
    4,  # 0x93
    3,  # 0x94
    3,  # 0x95
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    5,  # 0xA0
    0,  # 0xA1
    0,  # 0xA2
    0, 0, 0,
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


class Sequence:
    def __init__(self):
        self.commands = []
        self.trackOffset = [-1] * 16
        self.labelPosition = []
        self.labelName = []
        self.trackCount = 0
        self.tracksUsed = 0
        self.size = 0


class SSEQCommand(Sequence):
    def __init__(self, channel, location, position, command, argument):
        self.channel = channel
        self.location = location
        self.position = position
        self.command = command
        self.argument = argument
        self.binary = bytearray()


def variable_length_size(length):
    commandSize = 1
    for i in range(3):
        if length > 0x7F:
            length >>= 7
            commandSize += 1
    return commandSize


def write_variable_length(length):
    commandSize = 1
    out = 0
    for i in range(3):
        if length > 0x7F:
            out += (length & 0x7F)
            out <<= 8
            out |= 0x80
            length >>= 7
            commandSize += 1
    out += (length & 0x7F)
    return out, commandSize


def read_sseq(sdat):
    sseqSize = read_long(sdat, pos=sdat.pos + 0x8)
    sseqEnd = sdat.pos + sseqSize
    sdat.pos += 0x1C
    sseqFilePos = sdat.pos
    seq = Sequence()
    command = sdat.data[sdat.pos]
    if command == 0xFE:
        seq.tracksUsed = read_short(sdat, pos=sdat.pos + 1)
        sdat.pos += 3
        for i in range(16):
            if seq.tracksUsed & (1 << i):
                seq.trackCount += 1
    else:
        seq.tracksUsed = 1
        seq.trackCount = 1
        if sdat.pos == sseqEnd:
            seq.tracksUsed = 0
            seq.trackCount = 0
    command = sdat.data[sdat.pos]
    while command == 0x93:  # Track Pointer
        trackInfo = read_long(sdat, pos=sdat.pos + 1)
        seq.trackOffset[trackInfo & 0xFF] = (trackInfo >> 8)
        sdat.pos += 5
        command = sdat.data[sdat.pos]

    channel = -1
    sseqStart = sdat.pos - sseqFilePos
    sseqOffset = sdat.pos
    for i, offset in enumerate(seq.trackOffset):
        if offset > -1:
            seq.trackOffset[i] -= sseqStart
    seq.trackOffset[0] = 0
    command = 0xFF
    while sdat.pos < sseqEnd:
        if command in (0x94, 0xFD, 0xFF):  # Only look for channel changes when the last command was Jump, Return, or End
            for i, track in enumerate(seq.trackOffset):
                if track > -1 and i > channel:
                    if (sdat.pos - sseqOffset) >= track:
                        channel = i
                        location = 0
        command = sdat.data[sdat.pos]
        sdat.pos += 1
        if command in (0x94, 0x95):  # Jump or Call
            commandArgLen = sseqCmdArgs[command - 0x80]
            commandArg = (read_long(sdat, pos=sdat.pos) & 0xFFFFFF) - sseqStart
            if commandArg not in seq.labelPosition:
                seq.labelPosition.append(commandArg)
                if commandArg not in seq.trackOffset:
                    seq.labelName.append(f"Label_0x{hex(commandArg).lstrip('0x').rstrip('L').zfill(2).upper()}")
                else:
                    seq.labelName.append(f"Track_{seq.trackOffset.index(commandArg) + 1}")
                commandArg = seq.labelName[-1]
            else:
                commandArg = seq.labelName[seq.labelPosition.index(commandArg)]
            seq.commands.append(SSEQCommand(channel, location, (sdat.pos - sseqOffset) - 1, sseqCmdName[command - 0x80], commandArg))
            sdat.pos += commandArgLen
            seq.size = (sdat.pos - sseqOffset)
        elif command >= 0x80:
            commandName = sseqCmdName[command - 0x80]
            commandArgLen = sseqCmdArgs[command - 0x80]
            commandArg = None
            if commandName == "":
                seq.commands.append(SSEQCommand(channel, location, (sdat.pos - sseqOffset) - 1, "Unknown", command))
            else:
                if commandArgLen == -1:
                    commandArgLen = 0
                    commandArg = 0
                    for i in range(3):
                        if sdat.data[sdat.pos + commandArgLen] > 0x7F:
                            commandArg += (sdat.data[sdat.pos + commandArgLen] & 0x7F)
                            commandArg <<= 7
                            commandArgLen += 1
                    commandArg += (sdat.data[sdat.pos + commandArgLen] & 0x7F)
                    commandArgLen += 1
                elif commandArgLen > 0:
                    commandArg = int.from_bytes(sdat.data[sdat.pos : sdat.pos + commandArgLen], "little")
                seq.commands.append(SSEQCommand(channel, location, (sdat.pos - sseqOffset) - 1, commandName, commandArg))
                if command == 0x80:
                    location += commandArg
            sdat.pos += commandArgLen
            seq.size = (sdat.pos - sseqOffset)
        else:
            commandArgLen = 1
            commandArg = 0
            for i in range(3):
                if sdat.data[sdat.pos + commandArgLen] > 0x7F:
                    commandArg += (sdat.data[sdat.pos + commandArgLen] & 0x7F)
                    commandArg <<= 7
                    commandArgLen += 1
            commandArg += (sdat.data[sdat.pos + commandArgLen] & 0x7F)
            commandArgLen += 1
            if sdat.pos + commandArgLen < sseqEnd:
                seq.commands.append(SSEQCommand(channel, location, (sdat.pos - sseqOffset) - 1, "Note", [command, sdat.data[sdat.pos], commandArg]))
                sdat.pos += commandArgLen
                seq.size = (sdat.pos - sseqOffset)
    sdat.pos = sseqFilePos - 0x1C
    for i, cmd in enumerate(seq.commands):
        if cmd.position in seq.labelPosition:
            seq.labelPosition[seq.labelPosition.index(cmd.position)] = i
        if cmd.position in seq.trackOffset:
            seq.trackOffset[seq.trackOffset.index(cmd.position)] = i 
    return seq


def write_sseq_to_txt(seq, tempPath):
    channel = -1
    with open(f"{tempPath}.txt", "w") as sseqFile:
        for i, cmd in enumerate(seq.commands):
            if cmd.channel != channel:
                if i in seq.trackOffset:
                    channel = seq.trackOffset.index(i)
                    sseqFile.write(f"Track_{channel + 1}:\n")
            if i in seq.labelPosition:
                id = seq.labelPosition.index(i)
                sseqFile.write(f"{seq.labelName[id]}:\n")
                del seq.labelPosition[id]
                del seq.labelName[id]
            if cmd.command == "Note":
                sseqFile.write(f"\t{seqNote[cmd.argument[0] % 12]}{int(cmd.argument[0] / 12)},{cmd.argument[1]},{cmd.argument[2]}\n")
            elif cmd.command == "Unknown":
                sseqFile.write(f"\tUnknown_0x{hex(cmd.argument).lstrip('0x').rstrip('L').zfill(2).upper()}\n")
            else:
                if cmd.argument != None:
                    sseqFile.write(f"\t{cmd.command} {cmd.argument}\n")
                else:
                    if cmd.command in ("Return", "TrackEnd"):
                        sseqFile.write(f"\t{cmd.command}\n\n")
                    else:
                        sseqFile.write(f"\t{cmd.command}\n")
    

def read_sseq_from_txt(args, fName):
    testPath = f"{args.folder}/Files/{itemString[SEQ]}/{fName[:-5]}.txt"
    if not os.path.exists(testPath):
        raise Exception(f"Missing File:{testPath}")
    with open(testPath, "r") as sseqFile:
        done = False
        seq = Sequence()
        channel = -1
        position = 0  # position in reference to the number of bytes
        location = 0  # location of commands in reference to the song and channels
        while not done:
            thisLine = sseqFile.readline()
            if not thisLine:
                done = True
            thisLine = thisLine.split(";")[0]  # ignore anything commented out
            thisLine = thisLine.split("\n")[0]  # remove newline
            if thisLine != "":
                if thisLine.find("\t") == -1:  # label
                    thisLine = thisLine.replace(":", "")
                    if thisLine.split("_")[0] == "Track":
                        channel = int(thisLine.split("_")[1]) - 1
                        if channel > 15:
                            raise ValueError(f"Invalid track number {channel}")
                        seq.trackOffset[channel] = len(seq.commands)
                        location = 0
                        seq.trackCount += 1
                        seq.tracksUsed |= 1 << channel
                        if thisLine in seq.labelName:
                            raise ValueError(f"Label {thisLine} is defined more than once")
                    seq.labelName.append(thisLine)
                    seq.labelPosition.append(len(seq.commands))
                else:  # not a label
                    thisLine = thisLine.replace("\t", "").split(" ")
                    command = thisLine[0]
                    if command in sseqCmdName:
                        if len(thisLine) > 1:
                            seq.commands.append(SSEQCommand(channel, location, position, command, thisLine[1]))
                        else:
                            seq.commands.append(SSEQCommand(channel, location, position, command, None))
                        if command == "Delay":
                            location += int(thisLine[1])
                        commandSize = sseqCmdArgs[sseqCmdName.index(command)]
                        if commandSize == -1:
                            commandSize = variable_length_size(int(thisLine[1]))
                        position += commandSize + 1
                    elif command.split(",")[0][:2] in seqNote:  # Check if it's a note
                        param = command.split(",")
                        note = seqNote.index(param[0][:2]) + (int(param[0][2:]) * 12)
                        seq.commands.append(SSEQCommand(channel, location, position, "Note", [note, int(param[1]), int(param[2])]))
                        position += 2 + variable_length_size(int(param[2]))
                    elif command[0:10] == "Unknown_0x":
                        seq.commands.append(SSEQCommand(channel, location, position, "Unknown", int(command[10:12], 16)))
                        position += 1
                    else:
                        raise ValueError(f"Undefined Command {command}")
    seq.size = position
    return seq


def write_sseq(seq, args, fName):
    position = 0
    for cmd in seq.commands:  # fix positions and convert to binary
        cmd.position = position
        if cmd.command not in ("Jump", "Call"):
            if cmd.command == "Note":
                cmd.binary += cmd.argument[0].to_bytes(1, "little")
                cmd.binary += cmd.argument[1].to_bytes(1, "little")
                noteLength, size = write_variable_length(cmd.argument[2])
                cmd.binary += noteLength.to_bytes(size, "little")
            elif cmd.command == "Unknown":
                cmd.binary += cmd.argument.to_bytes(1, "little")
            else:
                try:
                    cmd.binary += (sseqCmdName.index(cmd.command) + 0x80).to_bytes(1, "little")
                except Exception:
                    raise ValueError(f"Undefined Command {cmd.command}")
                if cmd.argument != None:
                    commandSize = sseqCmdArgs[sseqCmdName.index(cmd.command)]
                    if commandSize == -1:
                        noteLength, size = write_variable_length(int(cmd.argument))
                        cmd.binary += noteLength.to_bytes(size, "little")
                    else:
                        cmd.binary += int(cmd.argument).to_bytes(commandSize, "little")
            position += len(cmd.binary)
        else:  # hardcode the size of jump/call since it will be converted to binary last
            position += 4
    seq.size = position

    headerSize = 0
    if seq.trackCount > 1:
        headerSize += 3 + ((seq.trackCount - 1) * 5)
    sseqSize = headerSize + 0x1C + seq.size
    sseqSize = (sseqSize + 3) & ~3  # pad to the next word
    sseqHeader = bytearray()
    sseqHeader += b'SSEQ'  # Header
    sseqHeader += b'\xFF\xFE\x00\x01'  # magic
    sseqHeader += sseqSize.to_bytes(4, byteorder='little')  # size
    sseqHeader += b'\x10\x00\x01\x00'  # structure size and blocks
    sseqHeader += b'DATA'
    sseqHeader += (sseqSize - 16).to_bytes(4, byteorder='little')  # struct size
    sseqHeader += b'\x1C\x00\x00\x00'  # sequenced data offset
    if seq.trackCount > 1:
        sseqHeader += b'\xFE'
        sseqHeader += seq.tracksUsed.to_bytes(2, byteorder='little')
    for i in range(1, 16):
        if seq.tracksUsed & (1 << i):
            sseqHeader += b'\x93'
            sseqHeader += i.to_bytes(1, byteorder='little')
            sseqHeader += (seq.commands[seq.trackOffset[i]].position + headerSize).to_bytes(3, byteorder='little')
    testPath = f"{args.folder}/Files/{itemString[SEQ]}/{fName}"
    with open(testPath, "wb") as sseqFile:
        sseqFile.write(sseqHeader)

        for cmd in seq.commands:  # fix label pointers
            if cmd.command in ("Jump", "Call"):
                if cmd.argument in seq.labelName:
                    cmd.argument = seq.commands[seq.labelPosition[seq.labelName.index(cmd.argument)]].position + headerSize
                else:
                    raise ValueError(f"Label \"{cmd.argument}\" is not defined")
                try:
                    cmd.binary += (sseqCmdName.index(cmd.command) + 0x80).to_bytes(1, "little")
                except Exception:
                    raise ValueError(f"Undefined Command {cmd.command}")
                if cmd.argument != None:
                    commandSize = sseqCmdArgs[sseqCmdName.index(cmd.command)]
                    if commandSize == -1:
                        noteLength, size = write_variable_length(int(cmd.argument))
                        cmd.binary += noteLength.to_bytes(size, "little")
                    else:
                        cmd.binary += int(cmd.argument).to_bytes(commandSize, "little")
            sseqFile.write(cmd.binary)
        sseqFile.write(b'\x00' * (sseqSize - (headerSize + 0x1C + seq.size)))
