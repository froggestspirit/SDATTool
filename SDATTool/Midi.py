import os
from const import itemString
from util import read_long, read_short
from Sseq import seqNote, Sequence, SSEQCommand

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


midiCmdName = (
    "NoteOff",
    "Note",
    "AfterTouch",
    "Controller",
    "Instrument",
    "AfterTouch2",  # temporary
    "mPitchBend",
    "Sys"
)


midiController = (
    "NoteOff",
    "Note",
    "AfterTouch",
    "Controller",
    "Instrument",
    "AfterTouch2",  # temporary
    "mPitchBend",
    "Sys"
)


midiCmdArgs = (  # -1 for variable length
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


def fix_label_pointers(id, seq):
    for i, pointer in enumerate(seq.trackOffset):
        if pointer >= id:
            seq.trackOffset[i] += 1
    for i, pointer in enumerate(seq.labelPosition):
        if pointer >= id:
            seq.labelPosition[i] += 1


def write_sseq_to_midi(seq, args, fName):
    midiHeader = bytearray()
    midiHeader += b'MThd'  # Header
    midiHeader += b'\x00\x00\x00\x06'  # header chunk size
    midiHeader += b'\x00\x01'  # Midi format 1
    midiHeader += seq.trackCount.to_bytes(2, byteorder='big')  # track count
    midiHeader += b'\x00\x30'  # delta-time

    # write to byte arrays in commands, while calculating track length
    channel = -1
    i = 0
    while i < len(seq.commands):
        cmd = seq.commands[i]
        if cmd.channel != channel:
            channel = cmd.channel
            location = 0
            lastDelay = 0
        if cmd.command == "Delay":
            lastDelay += cmd.argument
        else:
            noteLength, size = write_variable_length(lastDelay)
            seq.commands[i].binary += noteLength.to_bytes(size, "little")
            lastDelay = 0
            if cmd.command == 'Note':  # Unrolling the song should happen before adding the note off commands
                length = cmd.argument[2]
                id = i + 1
                try:
                    while length:
                        if seq.commands[id].command == "Delay":
                            length -= seq.commands[id].argument
                            if length < 0:
                                seq.commands[id].argument += length
                                seq.commands.insert(id + 1, SSEQCommand(channel, location, seq.commands[id].position, "Delay", -length))
                                fix_label_pointers(id + 1, seq)
                                length = 0
                        id += 1
                    seq.commands.insert(id, SSEQCommand(channel, location, cmd.position, "NoteOff", [cmd.argument[0], 0]))
                    fix_label_pointers(id, seq)
                    seq.commands[i].binary += (channel + 0x90).to_bytes(1, "big")
                    seq.commands[i].binary += cmd.argument[0].to_bytes(1, "big")
                    seq.commands[i].binary += cmd.argument[1].to_bytes(1, "big")
                except Exception:
                    del seq.commands[i].binary
                    seq.commands[i].binary = bytearray()
            elif cmd.command == 'NoteOff':
                seq.commands[i].binary += (channel + 0x80).to_bytes(1, "big")
                seq.commands[i].binary += cmd.argument[0].to_bytes(1, "big")
                seq.commands[i].binary += cmd.argument[1].to_bytes(1, "big")
            elif cmd.command in midiCmdName:
                seq.commands[i].binary += (channel + ((midiCmdName.index(cmd.command) + 8) << 4)).to_bytes(1, "big")
                seq.commands[i].binary += cmd.argument.to_bytes(1, "big")
            elif cmd.command in midiController:
                seq.commands[i].binary += (channel + 0xB0).to_bytes(1, "big")
                seq.commands[i].binary += midiController.index(cmd.command).to_bytes(1, "big")
            else:
                seq.commands[i].binary += b'\xFF\x01'
                if cmd.argument != None:
                    noteLength, size = write_variable_length(len(f"{cmd.command}|{cmd.argument}"))
                    seq.commands[i].binary += noteLength.to_bytes(size, "little")
                    seq.commands[i].binary += bytes(f"{cmd.command}|{cmd.argument}", 'utf-8')
                else:
                    noteLength, size = write_variable_length(len(f"{cmd.command}"))
                    seq.commands[i].binary += noteLength.to_bytes(size, "little")
                    seq.commands[i].binary += bytes(f"{cmd.command}", 'utf-8')
        i += 1

    channel = -1
    midiData = bytearray()
    chStart = [-1] * 16
    chEnd = [-1] * 16
    channelPointers = list(i for i in seq.trackOffset if i > -1)
    chPointerID = 0
    i = 0
    while i < len(seq.commands):
        cmd = seq.commands[i]
        if cmd.channel != channel:             
            channel = cmd.channel
            returnLoc = 0
            chStart[channel] = len(midiData)
        midiData += cmd.binary
        if cmd.command == "Call":
            returnLoc = i
            i = seq.labelPosition[seq.labelName.index(cmd.argument)] - 1
            cmd = seq.commands[i]
        elif cmd.command == "Return":
            if returnLoc:
                i = returnLoc
                returnLoc = 0
                cmd = seq.commands[i]
        elif cmd.command == "TrackEnd":
            midiData += b'\x00\xFF\x2F\x00'
            chEnd[channel] = len(midiData)
            chPointerID += 1
            if chPointerID < len(channelPointers):
                i = channelPointers[chPointerID] - 1
            else:
                i = len(seq.commands)
        i += 1

    testPath = f"{args.folder}/Files/{itemString[SEQ]}/{fName}.mid"
    with open(testPath, "wb") as midiFile:
        midiFile.write(midiHeader)
        for channel in range(16):
            if chStart[channel] > -1:
                midiFile.write(b'MTrk')
                midiFile.write(len(midiData[chStart[channel]:chEnd[channel]]).to_bytes(4, "big"))
                midiFile.write(midiData[chStart[channel]:chEnd[channel]])
