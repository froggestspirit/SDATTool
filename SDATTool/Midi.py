import os
from const import itemString
from util import read_long, read_short
from Sseq import seqNote, Sequence, SSEQCommand, sseqCmdName

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


def read_long(midiData, pos):
    return int.from_bytes(midiData[pos:pos + 4], 'big')


def read_short(midiData, pos):
    return int.from_bytes(midiData[pos:pos + 2], 'big')


def read_byte(midiData, pos):
    return int.from_bytes(midiData[pos:pos + 1], 'big')


def read_variable_length(midiData, pos):
    retVal = (int.from_bytes(midiData[pos:pos + 1], 'big') & 0x7F)
    for i in range(3):
        if (int.from_bytes(midiData[pos:pos + 1], 'big') & 0x80):
            pos += 1
            retVal = (retVal << 7) + (int.from_bytes(midiData[pos:pos + 1], 'big') & 0x7F)
    pos += 1
    return retVal, pos


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

    channel = -1
    i = 0
    while i < len(seq.commands):
        cmd = seq.commands[i]
        if cmd.channel != channel:
            channel = cmd.channel
            lastDelay = 0
            pitchBend = 0
        if cmd.command != 'Delay':
            if cmd.command == 'Note':
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
                seq.commands[i].binary += ((pitchBend << 6) & 0x7F).to_bytes(1, "little")
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
            elif cmd.command == 'Call':
                seq.commands[i].binary += b'\xFF\x01\x01'
                seq.commands[i].binary += bytes("{", 'utf-8')
            elif cmd.command == 'Return':
                seq.commands[i].binary += b'\xFF\x01\x01'
                seq.commands[i].binary += bytes("}", 'utf-8')
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
        if i in seq.labelPosition:
            commandOrder.append(len(seq.commands))
            seq.commands.append(SSEQCommand(cmd.channel, None, None, "Label", seq.labelName[seq.labelPosition.index(i)]))
            seq.commands[-1].binary += b'\xFF\x01'
            noteLength, size = write_variable_length(len(f"{seq.labelName[seq.labelPosition.index(i)]}"))
            seq.commands[-1].binary += noteLength.to_bytes(size, "little")
            seq.commands[-1].binary += bytes(f"{seq.labelName[seq.labelPosition.index(i)]}", 'utf-8')
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
                        if lastDelay > 0:
                            if seq.commands[i].argument > 0:
                                noteLength, size = write_variable_length(lastDelay)
                                midiData += noteLength.to_bytes(size, "little")
                                midiData += b"\xFF\x01\x05Dummy"
                                lastDelay = 0
                        lastDelay += seq.commands[i].argument
                chEndMidi[channel] = len(midiData)
                midiFile.write(b'MTrk')
                midiFile.write(len(midiData[chStartMidi[channel]:chEndMidi[channel]]).to_bytes(4, "big"))
                midiFile.write(midiData[chStartMidi[channel]:chEndMidi[channel]])


def read_sseq_from_midi(args, fName):
    testPath = f"{args.folder}/Files/{itemString[SEQ]}/{fName[:-5]}.mid"
    if not os.path.exists(testPath):
        raise Exception(f"Missing File:{testPath}")
    with open(testPath, "rb") as midiFile:
        midiData = bytearray(midiFile.read())
    seq = Sequence()
    if midiData[0:8] != b'MThd\x00\x00\x00\x06':
        raise ValueError("Not a valid midi header")
    if midiData[8:10] != b'\x00\x01':
        raise ValueError("Only Midi type 1 is supported")
    seq.trackCount = read_short(midiData, 10)
    timeDivision = read_short(midiData, 12)
    midiPos = 14
    trackSize = [-1] * 16
    trackStart = [-1] * 16
    trackEnd = [-1] * 16
    for ch in range(seq.trackCount):
        if midiData[midiPos:midiPos + 4] != b'MTrk':
            raise ValueError("Not a valid midi track header")
        midiPos += 4
        trackSize[ch] = read_long(midiData, midiPos)
        midiPos += 4
        trackStart[ch] = midiPos
        trackEnd[ch] = midiPos + trackSize[ch]
        location = 0
        activeNotes = []
        thisTrackStart = len(seq.commands)
        thisCh = 0
        endEarly = None
        while midiPos < trackEnd[ch]:
            delay, midiPos = read_variable_length(midiData, midiPos)
            if delay:  # write delay command
                if seq.commands[-1].command == "Delay":
                    seq.commands[-1].argument += delay
                else:
                    seq.commands.append(SSEQCommand(ch, location, 0, "Delay", delay))
                location += delay

            command = read_byte(midiData, midiPos)
            midiPos += 1
            commandType = command & 0xF0
            if commandType == 0x90:  # Note on
                thisCh = command & 0x0F
                note = read_byte(midiData, midiPos)
                midiPos += 1
                vel = read_byte(midiData, midiPos)
                midiPos += 1
                if vel:
                    activeNotes.append([note, len(seq.commands)])  # store the note's command index, to update it when note off is triggered
                    seq.commands.append(SSEQCommand(ch, location, 0, "Note", [note, vel, 0]))
                else:
                    id = 0
                    while id < len(activeNotes):
                        if note == activeNotes[id][0]:
                            seq.commands[activeNotes[id][1]].argument[2] = location - seq.commands[activeNotes[id][1]].location
                            del activeNotes[id]
                            break
            elif commandType == 0x80:  # Note off
                note = read_byte(midiData, midiPos)
                midiPos += 1
                vel = read_byte(midiData, midiPos)
                midiPos += 1
                id = 0
                while id < len(activeNotes):
                    if note == activeNotes[id][0]:
                        seq.commands[activeNotes[id][1]].argument[2] = location - seq.commands[activeNotes[id][1]].location
                        del activeNotes[id]
                        break
                    id += 1
            elif command == 0xFF:
                metaCommand = read_byte(midiData, midiPos)
                midiPos += 1
                metaLength = read_byte(midiData, midiPos)
                midiPos += 1
                if metaCommand == 0x2F:
                    seq.commands.append(SSEQCommand(ch, location, 0, "TrackEnd", None))
                    break
                elif metaCommand == 0x51:  # Tempo
                    tempo = int(60000000 / (read_long(midiData, midiPos) >> 8))
                    seq.commands.append(SSEQCommand(ch, location, 0, "Tempo", tempo))
                elif metaCommand == 0x01:
                    textCommand = midiData[midiPos:midiPos + metaLength].decode("utf-8")
                    if textCommand == "{":  # mark a subroutine, the following command needs to be a label
                        midiPos += metaLength
                        delay = read_byte(midiData, midiPos)
                        midiPos += 1
                        command = read_byte(midiData, midiPos)
                        midiPos += 1
                        metaCommand = read_byte(midiData, midiPos)
                        midiPos += 1
                        metaLength = read_byte(midiData, midiPos)
                        midiPos += 1
                        if delay == 0x00 and command == 0xFF and metaCommand == 0x01:
                            textCommand = midiData[midiPos:midiPos + metaLength].decode("utf-8")
                            if textCommand[:6] == "Label_":
                                seq.commands.append(SSEQCommand(ch, location, 0, "Call", textCommand))
                            else:
                                raise ValueError(f"Opening bracket is not followed by a label: {fName} at {midiPos}")
                        else:
                            raise ValueError(f"Opening bracket is not followed by a label: {fName} at {midiPos}")
                    elif textCommand == "}":
                        seq.commands.append(SSEQCommand(ch, location, 0, "Return", None))
                    # Check for labels, add them to label array
                    elif textCommand[:6] == "Label_":
                        if textCommand not in seq.labelName:
                            seq.labelName.append(textCommand)
                            seq.labelPosition.append(len(seq.commands))
                            seq.commands.append(SSEQCommand(ch, location, 0, "Dummy", None))  # Add to prevent merging delays
                    elif textCommand == "TrackEnd":
                        seq.commands.append(SSEQCommand(ch, location, 0, "TrackEnd", None))
                        endEarly = len(seq.commands)  # Mark where the end of the track should truly be, but continue (look for note ends)
                    else:
                        textCommand = textCommand.split("|")
                        if textCommand[0] in sseqCmdName:
                            if len(textCommand) > 1:
                                seq.commands.append(SSEQCommand(ch, location, 0, textCommand[0], textCommand[1]))
                            else:
                                seq.commands.append(SSEQCommand(ch, location, 0, textCommand[0], None))
                        elif textCommand[0] == "Unknown":
                            seq.commands.append(SSEQCommand(ch, location, 0, "Unknown", int(textCommand[1])))
                        elif textCommand[0] == "Dummy":
                            seq.commands.append(SSEQCommand(ch, location, 0, "Dummy", None))  # Add to prevent merging delays

                midiPos += metaLength
            elif commandType == 0xB0:
                thisCh = command & 0x0F
                controllerCmd = read_byte(midiData, midiPos)
                midiPos += 1
                if controllerCmd == 0x7E:
                    midiPos += 1
                    seq.commands.append(SSEQCommand(ch, location, 0, "Poly", 1))
                elif controllerCmd == 0x7F:
                    seq.commands.append(SSEQCommand(ch, location, 0, "Poly", 0))
                else:
                    seq.commands.append(SSEQCommand(ch, location, 0, midiController[controllerCmd], read_byte(midiData, midiPos)))
                midiPos += 1
            elif commandType == 0xE0:
                thisCh = command & 0x0F
                pitchBend = read_byte(midiData, midiPos) >> 6
                pitchBend += read_byte(midiData, midiPos + 1) << 1
                pitchBend = (pitchBend + 0x80) & 0xFF
                midiPos += 2
                seq.commands.append(SSEQCommand(ch, location, 0, "PitchBend", pitchBend))
            else:
                thisCh = command & 0x0F
                seq.commands.append(SSEQCommand(ch, location, 0, midiCmdName[(commandType >> 4) - 8], read_byte(midiData, midiPos)))
                midiPos += 1
        seq.trackOffset[thisCh] = thisTrackStart
        seq.tracksUsed |= 1 << thisCh
        if endEarly:
            del seq.commands[endEarly:]

    seq2 = Sequence()
    chAdjust = 0
    for ch in range(16):
        if (1 << ch) & seq.tracksUsed:
            readingSub = False
            subroutine = []
            seq.trackOffset[ch] = len(seq2.commands)
            for i, cmd in enumerate(seq.commands):  # reorder and handle subroutines
                if cmd.channel == chAdjust:
                    if i in seq.labelPosition:
                        seq.labelPosition[seq.labelPosition.index(i)] = len(seq2.commands)
                    if cmd.command == "Call":
                        seq2.commands.append(SSEQCommand(ch, cmd.location, 0, "Call", cmd.argument))
                        readingSub = True
                        if cmd.argument not in list(s[1] for s in subroutine):
                            subroutine.append([i, cmd.argument])
                    elif cmd.command == "Return":
                        readingSub = False
                    elif cmd.command == "Dummy":
                        pass  # ignore dummy commands
                    elif not readingSub:
                        seq2.commands.append(SSEQCommand(ch, cmd.location, 0, cmd.command, cmd.argument))
            subroutine.sort()
            for sub in subroutine:
                done = False
                i = sub[0]
                seq.labelName.append(sub[1])
                seq.labelPosition.append(len(seq2.commands))
                while not done:
                    cmd = seq.commands[i]
                    if cmd.channel == chAdjust:
                        if cmd.command not in ("Call", "Dummy"):
                            if cmd.command == "Return":
                                done = True
                            seq2.commands.append(SSEQCommand(ch, cmd.location, 0, cmd.command, cmd.argument))
                    i += 1
            chAdjust += 1
            del subroutine
    seq2.commands.append(SSEQCommand(ch, location, 0, "TrackEnd", None))
    seq2.tracksUsed = seq.tracksUsed
    seq2.labelPosition = seq.labelPosition
    seq2.labelName = seq.labelName
    seq2.trackOffset = seq.trackOffset
    seq2.trackCount = seq.trackCount
    return seq2
