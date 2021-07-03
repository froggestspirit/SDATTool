#!/usr/bin/python3
# SDAT-Tool by FroggestSpirit
version = "1.2.2"
# Unpacks and builds SDAT files
# Make backups, this can overwrite files without confirmation

import os
import hashlib
import time
import argparse
import json
from shutil import copyfile

from const import itemHeader, itemExt, itemString, infoBlockGroup, infoBlockGroupType, infoBlockGroupFile
from Sdat import SDAT
from util import read_long, read_short, get_string

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

progUsed = []
progUsedName = []


class MyEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


def unpack(args):  # Unpack
    print("Unpacking...")
    if not os.path.exists(args.folder):
        os.makedirs(args.folder)
    sdat = SDAT()
    with open(args.SDATfile, "rb") as infile:
        sdat.data = bytearray(infile.read())
    fileSize = len(sdat.data)
    sdat.pos = 8
    SDATSize = read_long(sdat)
    headerSize = read_short(sdat)
    blocks = read_short(sdat)
    if blocks == 4:
        symbOffset = read_long(sdat)
        symbSize = read_long(sdat)
    infoOffset = read_long(sdat)
    infoSize = read_long(sdat)
    fatOffset = read_long(sdat)
    fatSize = read_long(sdat)
    fileOffset = read_long(sdat)
    fileSize = read_long(sdat)

    # Symb Block
    seqarcName = []
    seqarcNameID = []
    if blocks == 4:
        sdat.pos = symbOffset + 8
        for i in range(8):
            sdat.itemSymbOffset[i] = read_long(sdat, pos=sdat.pos + (i * 4)) + symbOffset
        for i in range(8):
            if i != SEQARC:
                sdat.pos = sdat.itemSymbOffset[i]
                entries = read_long(sdat, pos=sdat.pos)
                for ii in range(entries):
                    sdat.pos = read_long(sdat, pos=sdat.itemSymbOffset[i] + 4 + (ii * 4)) + symbOffset
                    sdat.names[i].append(get_string(sdat))
            else:
                sdat.pos = sdat.itemSymbOffset[i]
                entries = read_long(sdat, pos=sdat.pos)
                for ii in range(entries):
                    sdat.pos = read_long(sdat, pos=sdat.itemSymbOffset[i] + 4 + (ii * 8)) + symbOffset
                    sdat.names[i].append(get_string(sdat))
                    sdat.pos = read_long(sdat, pos=sdat.itemSymbOffset[i] + 8 + (ii * 8)) + symbOffset
                    SEQARCSubOffset = sdat.pos
                    count = read_long(sdat, pos=sdat.pos)
                    for x in range(count):
                        sdat.pos = read_long(sdat, pos=SEQARCSubOffset + 4 + (x * 4)) + symbOffset
                        if entries > 0:
                            seqarcName.append(get_string(sdat))
                            seqarcNameID.append(ii)                            

    # Info Block
    sdat.infoBlock = sdat.InfoBlock(sdat)
    sdat.pos = infoOffset + 8
    for i in range(8):
        sdat.itemOffset[i] = read_long(sdat, pos=sdat.pos + (i * 4)) + infoOffset
    for i in range(8):
        sdat.pos = sdat.itemOffset[i]
        entries = read_long(sdat, pos=sdat.pos)
        for ii in range(entries):
            sdat.pos = read_long(sdat, pos=sdat.itemOffset[i] + 4 + (ii * 4)) + infoOffset
            if sdat.pos - infoOffset > 0x40:
                count = read_long(sdat, pos=sdat.pos)  # count is only used for group
                if blocks == 4 and ii < len(sdat.names[i]):
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
                sdat.infoBlock.seqarcInfo[-1].zippedName = [seqarcName[id] for id, num in enumerate(seqarcNameID) if num == ii]
    with open(f"{args.folder}/InfoBlock.json", "w") as outfile:
        outfile.write(json.dumps(sdat.infoBlock, cls=MyEncoder, indent=4)  # make the JSON file pretty at the expense of ugly code
            .replace(f"\n{' '*16}","")
            .replace(f"\n{' '*12}]","]")
            .replace(f"{{{' '*4}",f"\n{' '*16}{{")
            .replace(f",{' '*4}",", ")
            .replace(f',"',f",\n{' '*16}\"")
            .replace(f'["',f"[\n{' '*16}\"")
            .replace(f'{{\n{" "*12}"name": ""\n{" "*8}}},',f'{{"name": ""}},'))

    # FAT Block / File Block
    sdat.fileBlock = sdat.FileBlock()
    sdat.pos = fatOffset + 8
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
        sdat.pos = read_long(sdat, pos=fatOffset + 12 + (i * 16))
        tempSize = read_long(sdat, pos=fatOffset + 16 + (i * 16))
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
        sdat.fileBlock.file.append(FileBlock.File(f"{tempName}{tempExt}", tempType))
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
    with open(f"{args.folder}/FileBlock.json", "w") as outfile:
        outfile.write(json.dumps(sdat.fileBlock, cls=MyEncoder, indent=4))


def build(args):  # Build
    if not os.path.exists(f"{args.folder}/FileBlock.json"):
        raise Exception("Missing FileBlock.json\n")
    if not os.path.exists(f"{args.folder}/InfoBlock.json"):
        raise Exception("Missing InfoBlock.json\n")
    print("Building...")
    blocks = 4
    if args.noSymbBlock:
        blocks = 3

    with open(f"{args.folder}/FileBlock.json", "r") as infile:
        sdat.fileBlock = sdat.FileBlock()
        sdat.fileBlock.load(json.load(infile))
    with open(f"{args.folder}/InfoBlock.json", "r") as infile:
        sdat.infoBlock = sdat.InfoBlock()
        sdat.infoBlock.load(json.load(infile))

    if args.optimizeRAM:
        for i, item in enumerate(sdat.infoBlock.seqInfo):  # Check for SSEQ source files
            if item.name != "":
                fName = item.fileName
                if fName[-5:] == ".sseq":  # check for used instruments
                    if not fName in progUsedName:
                        tempInstUsed = []
                        testPath = f"{args.folder}/Files/{itemString[SEQ]}/{fName[:-5]}.txt"
                        if not os.path.exists(testPath):
                            raise Exception(f"Missing File:{testPath}")
                        with open(testPath, "r") as sseqFile:
                            done = False
                            sseqLines = []
                            numInst = 0
                            while not done:
                                thisLine = sseqFile.readline()
                                if not thisLine:
                                    done = True
                                thisLine = thisLine.split(";")[0]  # ignore anything commented out
                                thisLine = thisLine.split("\n")[0]  # remove newline
                                if thisLine != "":
                                    sseqLines.append(thisLine)
                            for channel in range(16):
                                done = False
                                if not f"Track_{channel}:" in sseqLines:
                                    done = True
                                else:
                                    curLine = sseqLines.index(f"Track_{channel}:") + 1
                                    curInst = 0
                                    retCall = -1
                                while not done:
                                    if sseqLines[curLine].find("\t") > -1:
                                        if sseqLines[curLine] == "\tTrackEnd":
                                            done = True
                                        elif sseqLines[curLine] == "\tReturn":
                                            if retCall > -1:
                                                curLine = retCall
                                                retCall = -1
                                        elif sseqLines[curLine].replace("\t","")[:2] in sseqNote:
                                            curNote = sseqNote.index(sseqLines[curLine].replace("\t","")[:2]) + (int(sseqLines[curLine][3]) * 12)
                                            if not (curInst << 7) + curNote in tempInstUsed:
                                                tempInstUsed.append((curInst << 7) + curNote)
                                                testvar = sseqNote.index(sseqLines[curLine].replace("\t","")[:2])
                                        elif sseqLines[curLine].replace("\t","").split(" ")[0] == "Instrument":
                                            curInst = int(sseqLines[curLine].replace("\t","").split(" ")[1])
                                        elif sseqLines[curLine].replace("\t","").split(" ")[0] == "Jump":
                                            done = True
                                        elif sseqLines[curLine].replace("\t","").split(" ")[0] == "Call":
                                            retCall = curLine
                                            t = sseqLines[curLine].replace('\t','').split(' ')[1]
                                            curLine = sseqLines.index(f"{t}:")
                                    curLine += 1
                                        
                        progUsedName.append(fName)
                        progUsed.append(tempInstUsed)
                    tempInstUsed = progUsed[progUsedName.index(fName)]
                    tempInstUsed.sort()
                    bnkID = list(bnk.name for bnk in sdat.infoBlock.bankInfo).index(sdat.infoBlock.seqInfo[i].bnk)
                    bnkFile = sdat.infoBlock.bankInfo[bnkID].fileName
                    sdat.fileBlock.file.append(sdat.fileBlock.File(f"{item.name}.sbnk", "BANK"))
                    sdat.fileBlock.file[-1].MD5 = sdat.fileBlock.file[list(file.name for file in sdat.fileBlock.file).index(bnkFile)].MD5
                    bnkFile = bnkFile.replace(".sbnk", ".txt")
                    usedSwav = [[], [], [], []]
                    orderSwav = []
                    with open(f"{args.folder}/Files/{itemString[BANK]}/{bnkFile}", "r") as sbnkIDFile:
                        done = False
                        sbnkLines = []
                        numInst = 0
                        curInst = -1
                        curInstType = -1
                        while not done:
                            thisLine = sbnkIDFile.readline()
                            if not thisLine:
                                done = True
                            thisLine = thisLine.split(";")[0]  # ignore anything commented out
                            thisLine = thisLine.split("\n")[0]  # remove newline
                            if thisLine != "" and thisLine.find("Unused") == -1:
                                if thisLine.find("\t") == -1:  # Don't count unused or sub definitions
                                    thisLine = thisLine.replace(" ","").split(",")
                                    curInst = int(thisLine[0])
                                    if curInst in ((prog >> 7) for prog in tempInstUsed):
                                        if thisLine[1] in ["Single", "PSG1", "PSG2", "PSG3"]:
                                            curInstType = -1
                                            if not int(thisLine[2]) in usedSwav[int(thisLine[3])]:
                                                usedSwav[int(thisLine[3])].append(int(thisLine[2]))
                                                orderSwav.append(int(thisLine[2]) + (int(thisLine[3]) << 16))
                                            thisLine[2] = str(orderSwav.index(int(thisLine[2]) + (int(thisLine[3]) << 16)))
                                            thisLine[3] = "0"
                                            sbnkLines.append(", ".join(thisLine))
                                        elif thisLine[1] == "Drums":
                                            curInstType = 0
                                            drumRange = [int(thisLine[2]), int(thisLine[3])]
                                            sbnkLines.append(", ".join(thisLine))
                                        elif thisLine[1] == "Keysplit":
                                            curInstType = 1
                                            keySplits = [-1, int(thisLine[2]), int(thisLine[3]), int(thisLine[4]), int(thisLine[5]), int(thisLine[6]), int(thisLine[7]), int(thisLine[8]), int(thisLine[9])]
                                            sbnkLines.append(", ".join(thisLine))
                                    else:
                                        sbnkLines.append(f"{thisLine[0]}, NULL")
                                        curInstType = -1
                                elif thisLine.find("\t") != -1:
                                    thisLine = thisLine.replace(" ","").split(",")
                                    if curInstType == 0:  # Drums
                                        if (curInst << 7) + drumRange[0] in tempInstUsed:
                                            if not int(thisLine[1]) in usedSwav[int(thisLine[2])]:
                                                usedSwav[int(thisLine[2])].append(int(thisLine[1]))
                                                orderSwav.append(int(thisLine[1]) + (int(thisLine[2]) << 16))
                                            thisLine[1] = str(orderSwav.index(int(thisLine[1]) + (int(thisLine[2]) << 16)))
                                            thisLine[2] = "0"
                                        else:
                                            thisLine[1] = "0"
                                            thisLine[2] = "0"
                                        sbnkLines.append(", ".join(thisLine))
                                        drumRange[0] += 1
                                    elif curInstType == 1:  # Keysplit
                                        found = False
                                        for split in range(keySplits[1] - keySplits[0]):
                                            if (curInst << 7) + split + keySplits[0] + 1 in tempInstUsed:
                                                found = True
                                        if found:
                                            if not int(thisLine[1]) in usedSwav[int(thisLine[2])]:
                                                usedSwav[int(thisLine[2])].append(int(thisLine[1]))
                                                orderSwav.append(int(thisLine[1]) + (int(thisLine[2]) << 16))
                                            thisLine[1] = str(orderSwav.index(int(thisLine[1]) + (int(thisLine[2]) << 16)))
                                            thisLine[2] = "0"
                                        else:
                                            thisLine[1] = "0"
                                            thisLine[2] = "0"
                                        sbnkLines.append(", ".join(thisLine))
                                        del keySplits[0]
                                else:
                                    sbnkLines.append(thisLine)
                    with open(f"{args.folder}/Files/{itemString[BANK]}/{item.name}.txt", "w") as sbnkIDFile:
                        for line in sbnkLines:
                            sbnkIDFile.write(f"{line}\n")

                    sdat.infoBlock.seqInfo[i].bnk = f"BANK_{item.name}"
                    sdat.infoBlock.bankInfo.append(sdat.infoBlock.BANKInfo("", blank=True))
                    sdat.infoBlock.bankInfo[-1].name = f"BANK_{item.name}"
                    sdat.infoBlock.bankInfo[-1].fileName = f"{item.name}.sbnk"
                    sdat.infoBlock.bankInfo[-1].unkA = sdat.infoBlock.bankInfo[bnkID].unkA
                    sdat.infoBlock.bankInfo[-1].wa[0] = f"WA_{item.name}"
                    sdat.infoBlock.wavarcInfo.append(sdat.infoBlock.BANKInfo("", blank=True))
                    sdat.infoBlock.wavarcInfo[-1].name = f"WA_{item.name}"
                    sdat.infoBlock.wavarcInfo[-1].fileName = f"{item.name}_WA.swar"
                    sdat.infoBlock.wavarcInfo[-1].unkA = 0
                    sdat.fileBlock.file.append(sdat.fileBlock.File(f"{item.name}_WA.swar", "WAVARC"))
                    sdat.fileBlock.file[-1].subFile = []
                    if not os.path.exists(f"{args.folder}/Files/{itemString[WAVARC]}/{item.name}_WA"):
                        os.makedirs(f"{args.folder}/Files/{itemString[WAVARC]}/{item.name}_WA")
                    swarFileID = [None, None, None, None]
                    for j in range(4):
                        if len(usedSwav[j]) > 0:
                            if sdat.infoBlock.bankInfo[bnkID].wa[j] != "":
                                swarID = list(swar.name for swar in sdat.infoBlock.wavarcInfo).index(sdat.infoBlock.bankInfo[bnkID].wa[j])
                                swarFileID[j] = list(swar.name for swar in sdat.fileBlock.file).index(sdat.infoBlock.wavarcInfo[swarID].fileName)
                    for sf in orderSwav:
                        sdat.fileBlock.file[-1].subFile.append(f"{sf >> 16}_{sdat.fileBlock.file[swarFileID[sf >> 16]].subFile[sf & 0xFFFF]}")
                        copyfile(f"{args.folder}/Files/{itemString[WAVARC]}/{sdat.fileBlock.file[swarFileID[sf >> 16]].name.split('.')[0]}/{sdat.fileBlock.file[swarFileID[sf >> 16]].subFile[sf & 0xFFFF]}", f"{args.folder}/Files/{itemString[WAVARC]}/{item.name}_WA/{sf >> 16}_{sdat.fileBlock.file[swarFileID[sf >> 16]].subFile[sf & 0xFFFF]}")

    if args.optimize:
        if args.optimizeSize:  #  These optimizations may break in-game, mainly used for generating a small SDAT for playback
            for group in infoBlockGroup:  # Remove empty entries in infoBlock
                i = 0
                exec(f"""while i < len(sdat.infoBlock.{group}):
                    if sdat.infoBlock.{group}[i].name == '':
                        del sdat.infoBlock.{group}[i]
                    else:
                        i += 1""")
            i = 0
            while i < len(sdat.infoBlock.bankInfo):  # Remove banks not referenced in the infoBlock
                name = sdat.infoBlock.bankInfo[i].name
                if name in list(item.bnk for item in sdat.infoBlock.seqInfo):
                    i += 1
                else:
                    del sdat.infoBlock.bankInfo[i]
            i = 0
            while i < len(sdat.infoBlock.wavarcInfo):  # Remove wavarc not referenced in the infoBlock
                name = sdat.infoBlock.wavarcInfo[i].name
                delete = True
                for wa in range(4):
                    if name in list(item.wa[wa] for item in sdat.infoBlock.bankInfo):
                        delete = False
                if delete:
                    del sdat.infoBlock.wavarcInfo[i]
                else:
                    i += 1
        i = 0
        while i < len(sdat.fileBlock.file):  # Remove files not referenced in the infoBlock
            name = sdat.fileBlock.file[i].name
            delete = True
            for group in infoBlockGroupFile:
                exec(f"""if name in list(item.fileName for item in (item for item in sdat.infoBlock.{group} if item.name != '')):
                    delete = False""")
            if delete:
                del sdat.fileBlock.file[i]
            else:
                i += 1
        if not args.optimizeRAM:
            i = 0
            while i < len(sdat.fileBlock.file):  # Remove files with duplicate MD5
                item = sdat.fileBlock.file[i]
                firstID = list(md5.MD5 for md5 in sdat.fileBlock.file[:i + 1]).index(item.MD5)
                if i != firstID:
                    sdat.infoBlock.replace_file(item.type, item.name, sdat.fileBlock.file[firstID].name)
                    del sdat.fileBlock.file[i]
                else:
                    i += 1

    for i in sdat.infoBlock.seqInfo:
        sdat.names[SEQ].append(i.name)
    seqarcSymbSubParent = []
    seqarcSymbSubName = []
    seqarcSymbSubCount = []
    for i in sdat.infoBlock.seqarcInfo:
        sdat.names[SEQARC].append(i.name)
        for ii in i.zippedName:
            seqarcSymbSubParent.append(len(sdat.names[SEQARC]) - 1)
            seqarcSymbSubName.append(ii)
        seqarcSymbSubCount.append(len(i.zippedName))
    for i in sdat.infoBlock.bankInfo:
        sdat.names[BANK].append(i.name)
    for i in sdat.infoBlock.wavarcInfo:
        sdat.names[WAVARC].append(i.name)
    for i in sdat.infoBlock.playerInfo:
        sdat.names[PLAYER].append(i.name)
    for i in sdat.infoBlock.groupInfo:
        sdat.names[GROUP].append(i.name)
    for i in sdat.infoBlock.player2Info:
        sdat.names[PLAYER2].append(i.name)
    for i in sdat.infoBlock.strmInfo:
        sdat.names[STRM].append(i.name)
    for i in sdat.fileBlock.file:
        sdat.names[FILE].append(i.name)
    sdat.itemCount = [len(sdat.names[SEQ]), len(sdat.names[SEQARC]), len(sdat.names[BANK]), len(sdat.names[WAVARC]), len(sdat.names[PLAYER]), len(sdat.names[GROUP]), len(sdat.names[PLAYER2]), len(sdat.names[STRM]), len(sdat.names[FILE])] 

    sdat.data = bytearray(b'SDAT')  # Header
    sdat.data += b'\xFF\xFE\x00\x01'  # Magic
    sdat.data += bytearray(4)  # File size
    append_short((blocks + 4) * 8)  # Header size
    append_short(blocks)  # Blocks
    sdat.data += bytearray((blocks + 2) * 8)  # reserve space for the offsets and sizes
    headeri = 0  # help point back to the block offsets and sizes when ready to write

    if blocks == 4:  # symbBlock
        symbBlockOffset = len(sdat.data)
        sdat.data += b'SYMB'  # Header
        sdat.data += bytearray(4)  # symbBlock size
        sdat.data += bytearray(8 * 4)  # reserve space for the offsets
        sdat.data += bytearray(24)  # reserved bytes

        for i in range(8):
            sdat.itemSymbOffset[i] = len(sdat.data)
            write_long(symbBlockOffset + (i * 4) + 8, sdat.itemSymbOffset[i] - symbBlockOffset)
            append_long(sdat.itemCount[i])
            if i != SEQARC:
                sdat.data += bytearray(sdat.itemCount[i] * 4)
            else:
                seqarcSymbSubOffset = []
                sdat.data += bytearray(sdat.itemCount[i] * 8)  # this has sub-groups
                for ii in range(sdat.itemCount[i]):
                    write_long((sdat.itemSymbOffset[i] + 8) + (ii * 8), len(sdat.data) - symbBlockOffset)
                    seqarcSymbSubOffset.append(len(sdat.data))
                    append_long(seqarcSymbSubCount[ii])
                    sdat.data += bytearray(seqarcSymbSubCount[ii] * 4)

        for i in range(8):
            if i != SEQARC:
                for ii in range(sdat.itemCount[i]):
                    if sdat.names[i][ii] != "":
                        write_long((sdat.itemSymbOffset[i] + 4) + (ii * 4), len(sdat.data) - symbBlockOffset)
                        for x, character in enumerate(sdat.names[i][ii]):
                            append_byte(ord(character))
                        append_byte(0)  # terminate string
            else:
                for ii in range(sdat.itemCount[i]):
                    if sdat.names[i][ii] != "":
                        write_long((sdat.itemSymbOffset[i] + 4) + (ii * 8), len(sdat.data) - symbBlockOffset)
                        for x, character in enumerate(sdat.names[i][ii]):
                            append_byte(ord(character))
                        append_byte(0)  # terminate string
                        curSeqarcSub = 0
                        for subi, name in enumerate(seqarcSymbSubName):
                            if seqarcSymbSubParent[subi] == ii:
                                if name != "":
                                    write_long((seqarcSymbSubOffset[ii] + 4) + (curSeqarcSub * 4), len(sdat.data) - symbBlockOffset)
                                    for x, character in enumerate(name):
                                        append_byte(ord(character))
                                    append_byte(0)  # terminate string
                                curSeqarcSub += 1

        write_long(16, symbBlockOffset)
        write_long(20, len(sdat.data) - symbBlockOffset)
        headeri += 1
        sdat.data += bytearray((4 - (len(sdat.data) & 3)) & 3)  # pad to the nearest 0x04 byte alignment
        write_long(symbBlockOffset + 4, len(sdat.data) - symbBlockOffset)

    infoBlockOffset = len(sdat.data)  # infoBlock
    sdat.data += b'INFO'  # Header
    sdat.data += bytearray(4)  # File size
    sdat.data += bytearray(8 * 4)  # reserve space for the offsets
    sdat.data += bytearray(24)  # reserved bytes

    for i in range(8):
        sdat.itemOffset[i] = len(sdat.data)
        write_long(infoBlockOffset + (i * 4) + 8, sdat.itemOffset[i] - infoBlockOffset)
        append_long(sdat.itemCount[i])
        sdat.data += bytearray(sdat.itemCount[i] * 4)
        for ii in range(sdat.itemCount[i]):
            write_long((sdat.itemOffset[i] + 4) + (ii * 4), len(sdat.data) - infoBlockOffset)
            tempSize = len(sdat.data)
            exec(f"sdat.infoBlock.write(sdat.infoBlock.{infoBlockGroup[i]}, ii)")
            if tempSize == len(sdat.data):  # Null out the pointer for null items
                write_long((sdat.itemOffset[i] + 4) + (ii * 4), 0)

    write_long(16 + (headeri * 8), infoBlockOffset)
    write_long(20 + (headeri * 8), len(sdat.data) - infoBlockOffset)
    headeri += 1
    sdat.data += bytearray((4 - (len(sdat.data) & 3)) & 3)  # pad to the nearest 0x04 byte alignment
    write_long(infoBlockOffset + 4, len(sdat.data) - infoBlockOffset)

    fatBlockOffset = len(sdat.data)  # fatBlock
    sdat.data += b'FAT\x20'  # Header
    append_long((sdat.itemCount[FILE] * 16) + 12)  # fatBlock size
    append_long(sdat.itemCount[FILE])  # number of FAT records
    sdat.data += bytearray((sdat.itemCount[FILE] * 16))

    write_long(16 + (headeri * 8), fatBlockOffset)
    write_long(20 + (headeri * 8), len(sdat.data) - fatBlockOffset)
    headeri += 1
    sdat.data += bytearray((4 - (len(sdat.data) & 3)) & 3)  # pad to the nearest 0x04 byte alignment
    write_long(fatBlockOffset + 4, len(sdat.data) - fatBlockOffset)

    fileBlockOffset = len(sdat.data)  # fileBlock
    sdat.data += b'FILE'  # Header
    sdat.data += bytearray(4)  # fileBlock size
    append_long(sdat.itemCount[FILE])  # number of files
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

    curFile = 0
    tFileBuffer = []
    for i, fName in enumerate(sdat.names[FILE]):  # Pack the binary files
        testPath = f"{args.folder}/Files/{itemString[itemExt.index(fName[-5:])]}/{fName}"
        if not os.path.exists(testPath):
            testPath = f"{args.folder}/Files/{fName}"
            if not os.path.exists(testPath):
                raise Exception(f"Missing File:{testPath}")
        curFileLoc = (len(sdat.data) + sum(len(tf) for tf in tFileBuffer))
        write_long((curFile * 16) + 12 + fatBlockOffset, curFileLoc)  # write file pointer to the fatBlock
        with open(testPath, "rb") as tempFile:
            tFileBuffer.append(bytearray(tempFile.read()))
        write_long((curFile * 16) + 16 + fatBlockOffset, len(tFileBuffer[curFile]))  # write file size to the fatBlock

        while (len(tFileBuffer[curFile]) & 0xFFFFFFE0) != len(tFileBuffer[curFile]):
            tFileBuffer[curFile] += b'\x00'  # pad to the nearest 0x20 byte alignment
        curFile += 1
    write_long(16 + (headeri * 8), fileBlockOffset)
    write_long(20 + (headeri * 8), (len(sdat.data) + sum(len(tf) for tf in tFileBuffer)) - fileBlockOffset)
    write_long(fileBlockOffset + 4, (len(sdat.data) + sum(len(tf) for tf in tFileBuffer)) - fileBlockOffset)  # write fileBlock size
    write_long(8, (len(sdat.data) + sum(len(tf) for tf in tFileBuffer)))  # write file size
    with open(args.SDATfile, "wb") as outfile:
        outfile.write(sdat.data)
        for i, tFile in enumerate(tFileBuffer):
            outfile.write(tFile)


def main():
    parser = argparse.ArgumentParser(description=f"SDAT-Tool {version}: Unpack/Pack NDS SDAT Files")
    parser.add_argument("SDATfile")
    parser.add_argument("folder", nargs="?")
    mode_grp = parser.add_mutually_exclusive_group(required=True)
    mode_grp.add_argument("-u", "--unpack", dest="mode", action="store_false")
    mode_grp.add_argument("-b", "--build", dest="mode", action="store_true")
    parser.add_argument("-o", "--optimize", dest="optimize", action="store_true", help="Remove unused and duplicate files")
    parser.add_argument("-os", "--optimize_size", dest="optimizeSize", action="store_true", help="Build Optimized for filesize")
    parser.add_argument("-or", "--optimize_ram", dest="optimizeRAM", action="store_true", help="Build Optimized for RAM")
    parser.add_argument("-ns", "--noSymbBlock", dest="noSymbBlock", action="store_true", help="Build without a SymbBlock")
    args = parser.parse_args()

    if args.optimizeSize or args.optimizeRAM:
        args.optimize = True

    if args.optimizeRAM & args.optimizeSize:
        raise ValueError("Cannot optimize for size and RAM")
    if args.SDATfile.lower().find(".sdat") == -1:
        raise ValueError("File is not a SDAT file")
    if not args.folder:
        args.folder = args.SDATfile.lower().replace(".sdat","")
    if args.SDATfile.lower() == args.folder.lower():
        raise ValueError("Input and output cannot match")

    ts = time.time()
    if not args.mode:
        unpack(args)
    else:
        build(args)
    ts2 = time.time() - ts
    print(f"Done: {ts2}s")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        raise Exception(e)
