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


class SSEQCommand:
    def __init__(self, channel, location, position, command, argument):
        self.channel = channel
        self.position = location
        self.position = position
        self.command = command
        self.argument = argument
        self.binary = bytearray()


def unpack_sseq(sdat, tempPath):
    sseqSize = read_long(sdat, pos=sdat.pos + 0x14)
    sseqEnd = sdat.pos + 16 + sseqSize
    sdat.pos += 0x1C
    sseqStart = sdat.pos

    # Run through first to calculate labels
    trackOffset = [0] * 16
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
                if commandName in ("Return", "TrackEnd"):
                    commandName = f"{commandName}\n"
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
                if sdat.pos <= sseqEnd:
                    sseqFile.write(f"\t{sseqNote[command % 12]}{int(command / 12)},{velocity},{commandArg}\n")
    sdat.pos = sseqStart - 0x1C


def build_sseq(sdat, args, fName):  # unfinished, in progress
    testPath = f"{args.folder}/Files/{itemString[SEQ]}/{fName[:-5]}.txt"
    if not os.path.exists(testPath):
        raise Exception(f"Missing File:{testPath}")
    with open(testPath, "r") as sseqFile:
        done = False
        commands = []
        trackOffset = [0] * 16
        labelName = []
        labelPosition = []
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
                        channel = int(thisLine.split("_")[1])
                        trackOffset[channel] = position
                        location = 0
                        if thisLine in labelName:
                            raise ValueError(f"Label {thisLine} is defined more than once")
                    labelName.append(thisLine)
                    labelPosition.append(position)
                else:  # not a label
                    thisLine = thisLine.replace("\t", "").split(" ")
                    command = thisLine[0]
                    if command in sseqCmdName:
                        if len(thisLine) > 1:
                            commands.append(SSEQCommand(channel, location, position, command, thisLine[1]))
                        else:
                            commands.append(SSEQCommand(channel, location, position, command, None))
                        if command == "Delay":
                            location += int(thisLine[1])
                        commandSize = sseqCmdArgs[sseqCmdName.index(command)]
                        if commandSize == -1:
                            delay = int(thisLine[1])
                            commandSize = 1
                            delay >>= 7
                            for i in range(3):
                                if delay:
                                    delay >>= 7
                                    commandSize += 1
                        position += commandSize + 1
                    elif command.split(",")[0][:2] in sseqNote:  # Check if it's a note
                        param = command.split(",")
                        note = sseqNote.index(param[0][:2]) + (int(param[0][2:]) * 12)
                        commands.append(SSEQCommand(channel, location, position, "Note", note + (int(param[1]) << 8) + (int(param[2]) << 16)))
                    else:
                        raise ValueError(f"Undefined Command {command}")
    # get the number of channels, calculate the header size, so the relative pointers can have an offset
    
    for cmd in commands:  # fix label pointers
        if cmd.command in ("Jump", "Call"):
            if cmd.argument in labelName:
                cmd.argument = labelPosition[labelName.index(cmd.argument)]
            else:
                raise ValueError(f"Label \"{cmd.argument}\" is not defined")
    for cmd in commands:
        if cmd.command == "Note":
            cmd.binary += cmd.argument.to_bytes(3, "little")
        else:
            try:
                cmd.binary += (sseqCmdName.index(cmd.command) + 0x80).to_bytes(1, "little")
            except Exception:
                raise ValueError(f"Undefined Command {cmd.command}")
            if cmd.argument:
                commandSize = sseqCmdArgs[sseqCmdName.index(cmd.command)]
                if commandSize == -1:
                    delay = int(cmd.argument)
                    commandSize = 1
                    delay >>= 7
                    for i in range(3):
                        if delay:
                            delay >>= 7
                            commandSize += 1
                cmd.binary += int(cmd.argument).to_bytes(commandSize, "little")
    testPath = f"{args.folder}/Files/{itemString[SEQ]}/{fName}"
    with open(testPath, "wb") as sseqFile:
        for cmd in commands:
            sseqFile.write(cmd.binary)
            print(f"{cmd.command}: {cmd.binary}")
    #pad to nearest word
    
