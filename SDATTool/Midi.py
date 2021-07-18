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
    "_PitchBend",
    "Sys"
)


midiController = (
    "", "", "", "", "", "PortamentoTime", "PitchBendRange", "Volume", "", "", "Pan", "Expression", "", "", "", "",
    "", "", "", "", "MasterVolume", "Transpose", "Priority", "Tie", "ModDepth", "ModSpeed", "ModType", "ModRange", "", "", "", "",
    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    "", "PortamentoOnOff", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    "", "", "", "", "PortamentoControl", "Attack", "Decay", "Sustain", "Release", "", "", "", "", "", "", "",
    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    "", "", "", "", "", "", "", ""
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
            lastDelay = 0
            pitchBend = 0
        if cmd.command != 'Delay':
            if cmd.command == 'Note':  # Unrolling the song should happen before adding the note off commands
                seq.commands[i].binary += (channel + 0x90).to_bytes(1, "big")
                seq.commands[i].binary += cmd.argument[0].to_bytes(1, "big")
                seq.commands[i].binary += cmd.argument[1].to_bytes(1, "big")
            elif cmd.command in midiCmdName:
                seq.commands[i].binary += (channel + ((midiCmdName.index(cmd.command) + 8) << 4)).to_bytes(1, "big")
                seq.commands[i].binary += cmd.argument.to_bytes(1, "big")
            elif cmd.command in midiController:
                seq.commands[i].binary += (channel + 0xB0).to_bytes(1, "big")
                seq.commands[i].binary += midiController.index(cmd.command).to_bytes(1, "big")
                seq.commands[i].binary += cmd.argument.to_bytes(1, "big")
            elif cmd.command == 'PitchBend':
                seq.commands[i].binary += (channel + 0xE0).to_bytes(1, "big")
                pitchBend = (cmd.argument + 0x80) & 0xFF
                seq.commands[i].binary += ((pitchBend << 7) & 0x7F).to_bytes(1, "little")
                seq.commands[i].binary += (pitchBend >> 1).to_bytes(1, "little")
            elif cmd.command == 'Tempo':
                seq.commands[i].binary += b'\xFF\x51\x03'
                seq.commands[i].binary += int(60000000 / cmd.argument).to_bytes(3, "big")
            elif cmd.command == 'Poly':
                seq.commands[i].binary += (channel + 0xB0).to_bytes(1, "big")
                if cmd.argument:  # Mono mode
                    seq.commands[i].binary += b'\x7E'
                    seq.commands[i].binary += channel.to_bytes(1, "big")
                    seq.commands[i].binary += b'\x01'
                else:  # Poly mode
                    seq.commands[i].binary += b'\x7F'
                    seq.commands[i].binary += channel.to_bytes(1, "big")
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
    commandOrder = []
    midiData = bytearray()
    chStart = [-1] * 16
    chEnd = [-1] * 16
    channelPointers = list(i for i in seq.trackOffset if i > -1)
    chPointerID = 0
    activeNotes = []
    i = 0
    while i < len(seq.commands):
        cmd = seq.commands[i]
        if cmd.command == "Delay":
            delayLeft = thisDelay = cmd.argument
            notesOn = list(n for n in activeNotes if n[0] > -1)
            notesOn.sort()
            for id, note in enumerate(notesOn):
                if note[0] <= delayLeft:
                    delay = note[0]
                    for n in range(id, len(notesOn)):
                        notesOn[n][0] -= delay
                    commandOrder.append(len(seq.commands))
                    seq.commands.append(SSEQCommand(channel, None, None, "Delay", delay))
                    delayLeft -= delay
                if note[0] == 0:
                    commandOrder.append(len(seq.commands))
                    seq.commands.append(SSEQCommand(channel, None, None, "NoteOff", [note[1], note[2]]))
                    seq.commands[-1].binary += (channel + 0x80).to_bytes(1, "big")
                    seq.commands[-1].binary += note[1].to_bytes(1, "big")
                    seq.commands[-1].binary += note[2].to_bytes(1, "big")
            commandOrder.append(len(seq.commands))
            seq.commands.append(SSEQCommand(channel, None, None, "Delay", delayLeft - thisDelay)) # this will be <=0
            id = 0
            while id < len(activeNotes):
                activeNotes[id][0] -= delayLeft
                if activeNotes[id][0] <= 0:
                    del activeNotes[id]
                else:
                    id +=1

        if cmd.channel != channel:  
            notesOn = list(n for n in activeNotes if n[0] > -1)
            notesOn.sort()
            for id, note in enumerate(notesOn):
                delay = note[0]
                for n in range(id, len(notesOn)):
                    notesOn[n][0] -= delay
                commandOrder.append(len(seq.commands))
                seq.commands.append(SSEQCommand(channel, None, None, "Delay", delay))
                commandOrder.append(len(seq.commands))
                seq.commands.append(SSEQCommand(channel, None, None, "NoteOff", [note[1], note[2]]))
                seq.commands[-1].binary += (channel + 0x80).to_bytes(1, "big")
                seq.commands[-1].binary += note[1].to_bytes(1, "big")
                seq.commands[-1].binary += note[2].to_bytes(1, "big")
            if channel > -1:
                commandOrder.append(len(seq.commands))
                seq.commands.append(SSEQCommand(channel, None, None, "TrackEnd", None))
                seq.commands[-1].binary = b'\xFF\x2F\x00'
                chEnd[channel] = len(commandOrder)
            channel = cmd.channel
            returnLoc = 0
            chStart[channel] = len(commandOrder)
            del activeNotes
            activeNotes = []
            
        commandOrder.append(i)
        if cmd.command == "Note":
            activeNotes.append([cmd.argument[2], cmd.argument[0], cmd.argument[1]])
        elif cmd.command == "Call":
            returnLoc = i
            i = seq.labelPosition[seq.labelName.index(cmd.argument)] - 1
        elif cmd.command == "Return":
            if returnLoc:
                i = returnLoc
                returnLoc = 0
        elif cmd.command == "TrackEnd":
            chPointerID += 1
            if chPointerID < len(channelPointers):
                i = channelPointers[chPointerID] - 1
            else:
                i = len(seq.commands)
        i += 1


    notesOn = list(n for n in activeNotes if n[0] > -1)
    notesOn.sort()
    for id, note in enumerate(notesOn):
        delay = note[0]
        for n in range(id, len(notesOn)):
            notesOn[n][0] -= delay
        commandOrder.append(len(seq.commands))
        seq.commands.append(SSEQCommand(channel, None, None, "Delay", delay))
        commandOrder.append(len(seq.commands))
        seq.commands.append(SSEQCommand(channel, None, None, "NoteOff", [note[1], note[2]]))
        seq.commands[-1].binary += (channel + 0x80).to_bytes(1, "big")
        seq.commands[-1].binary += note[1].to_bytes(1, "big")
        seq.commands[-1].binary += note[2].to_bytes(1, "big")
    if channel > -1:
        commandOrder.append(len(seq.commands))
        seq.commands.append(SSEQCommand(channel, None, None, "TrackEnd", None))
        seq.commands[-1].binary = b'\xFF\x2F\x00'
        chEnd[channel] = len(commandOrder)

    chStartMidi = [-1] * 16
    chEndMidi = [-1] * 16
    testPath = f"{args.folder}/Files/{itemString[SEQ]}/{fName}.mid"
    with open(testPath, "wb") as midiFile:
        midiFile.write(midiHeader)
        for channel in range(16):
            if chStart[channel] != chEnd[channel]:
                chStartMidi[channel] = len(midiData)
                lastDelay = 0
                for i in commandOrder[chStart[channel]:chEnd[channel]]:
                    if len(seq.commands[i].binary):
                        noteLength, size = write_variable_length(lastDelay)
                        midiData += noteLength.to_bytes(size, "little")
                        midiData += seq.commands[i].binary
                        lastDelay = 0
                    elif seq.commands[i].command == "Delay":
                        lastDelay += seq.commands[i].argument
                chEndMidi[channel] = len(midiData)
                midiFile.write(b'MTrk')
                midiFile.write(len(midiData[chStartMidi[channel]:chEndMidi[channel]]).to_bytes(4, "big"))
                midiFile.write(midiData[chStartMidi[channel]:chEndMidi[channel]])
