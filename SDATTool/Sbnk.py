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


def unpack_sbnk(sdat, tempPath):
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


def build_sbnk(sdat, args, fName):
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