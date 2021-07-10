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


def write_sseq_to_midi(seq, args, fName):
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
            seq.trackOffset[i] += headerSize
            sseqHeader += b'\x93'
            sseqHeader += i.to_bytes(1, byteorder='little')
            sseqHeader += seq.trackOffset[i].to_bytes(3, byteorder='little')
    testPath = f"{args.folder}/Files/{itemString[SEQ]}/{fName}.sseq"
    with open(testPath, "wb") as sseqFile:
        sseqFile.write(sseqHeader)
        for cmd in seq.commands:  # fix label pointers
            if cmd.command in ("Jump", "Call"):
                if cmd.argument in seq.labelName:
                    cmd.argument = seq.labelPosition[seq.labelName.index(cmd.argument)] + headerSize
                else:
                    raise ValueError(f"Label \"{cmd.argument}\" is not defined")
            if cmd.command == "Note":
                cmd.binary += cmd.argument[0].to_bytes(1, "little")
                cmd.binary += cmd.argument[1].to_bytes(1, "little")
                noteLength, size = write_variable_length(cmd.argument[2])
                cmd.binary += noteLength.to_bytes(size, "little")
            elif cmd.command == "Unknown":
                cmd.binary += cmd.argument.to_bytes(1, "little")
            else:
                try:
                    cmd.binary += (midiCmdName.index(cmd.command) + 0x80).to_bytes(1, "little")
                except Exception:
                    raise ValueError(f"Undefined Command {cmd.command}")
                if cmd.argument != None:
                    commandSize = midiCmdArgs[midiCmdName.index(cmd.command)]
                    if commandSize == -1:
                        noteLength, size = write_variable_length(int(cmd.argument))
                        cmd.binary += noteLength.to_bytes(size, "little")
                    else:
                        cmd.binary += int(cmd.argument).to_bytes(commandSize, "little")
            sseqFile.write(cmd.binary)
        sseqFile.write(b'\x00' * (sseqSize - (headerSize + 0x1C + seq.size)))
