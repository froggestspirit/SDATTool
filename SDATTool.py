#SDAT-Tool by FroggestSpirit
version = "0.9.1"
#Unpacks and builds SDAT files
#Make backups, this can overwrite files without confirmation

import sys
import os
import math
import hashlib
import time

ts = time.time()
sysargv = sys.argv
echo = True
mode = 0
SDATPos = 0
calcMD5 = False
optimize = False
skipSymbBlock = False
skipFileOrder = False
removeUnused = False

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

itemString = [
    "SEQ",
    "SEQARC",
    "BANK",
    "WAVARC",
    "PLAYER",
    "GROUP",
    "PLAYER2",
    "STRM",
    "FILE"
]

itemParamString = [
    "SEQ(name,fileName,?,bnk,vol,cpr,ppr,ply,?[2]){\n",
    "SEQARC(name,fileName,?){\n",
    "BANK(name,fileName,?,wa[4]){\n",
    "WAVARC(name,fileName,?){\n",
    "PLAYER(name,?,padding[3],?){\n",
    "GROUP(name,count[type,entries]){\n",
    "PLAYER2(name,count,v[16],reserved[7]){\n",
    "STRM(name,fileName,?,vol,pri,ply,reserved[5]){\n"
]

itemParams = [
    [FILE,SHORT,BANK,BYTE,BYTE,BYTE,PLAYER,BYTE,BYTE],
    [FILE,SHORT],
    [FILE,SHORT,WAVARC,WAVARC,WAVARC,WAVARC],
    [FILE,SHORT],
    [BYTE,BYTE,BYTE,BYTE,LONG],
    [LONG],
    [BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE],
    [FILE,SHORT,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE]
]

itemExt = [
    ".sseq",
    ".ssar",
    ".sbnk",
    ".swar",
    "",
    "",
    "",
    ".strm"
]

itemHeader = [
    "SSEQ",
    "SSAR",
    "SBNK",
    "SWAR",
    "",
    "",
    "",
    "STRM"
]

itemOffset = [0,0,0,0,0,0,0,0,0]
itemSymbOffset = [0,0,0,0,0,0,0,0,0]
itemCount = [0,0,0,0,0,0,0,0,0]
itemData = [[],[],[],[],[],[],[],[],[]]
names = [[],[],[],[],[],[],[],[],[]]
namesUsed = [[],[],[],[],[],[],[],[],[]]
fileType = []
fileNameID = []
fileMD5 = []
fileAll = []
fileAllMD5 = []

SDAT = []

def read_long(pos):
    return (SDAT[pos + 3] * 0x1000000) + (SDAT[pos + 2] * 0x10000) + (SDAT[pos + 1] * 0x100) + SDAT[pos]

def read_short(pos):
    return (SDAT[pos + 1] * 0x100) + SDAT[pos]

def add_fileName(name):
    if name not in names[FILE]:
        if optimize:
            testPath = sysargv[outfileArg] + "/Files/" + itemString[itemExt.index(name[-5:])] + "/" + name
            if not os.path.exists(testPath):
                testPath = sysargv[outfileArg] + "/Files/" + name
            if os.path.exists(testPath):
                tempFile = open(testPath, "rb")
                tFileBuffer = []
                tFileBuffer = tempFile.read()
                tempFile.close()
                thisMD5 = hashlib.md5(tFileBuffer)
                fileAll.append(name)
                fileAllMD5.append(thisMD5.hexdigest())
                if thisMD5.hexdigest() not in fileMD5:
                    itemCount[FILE] += 1
                    fileMD5.append(thisMD5.hexdigest())
                    names[FILE].append(name)
            else:#can't calculate MD5
                fileAll.append(name)
                fileAllMD5.append(itemCount[FILE])
                fileMD5.append(itemCount[FILE])
                itemCount[FILE] += 1
                names[FILE].append(name)
        else:
            itemCount[FILE] += 1
            names[FILE].append(name)

def check_unused(removeFlag, item, string): #return true to add the item, return false to skip it (unused)
    if not removeFlag: #skip this if the build is removing unused entries
        return True
    if string == "NULL": #skip item if null
        return False
    if item in (SEQ, SEQARC, GROUP, PLAYER2, STRM): #None of these get referenced from other items(?), so they should all be included
        return True
    if string in namesUsed[item]:
        return True
    return False

def get_params(tList):
    global SDATPos
    retString = ""
    for i, listItem in enumerate(tList):
        tempString = ""
        if i > 0:
            retString += ","
        if listItem == BYTE:
            tempString = str(SDAT[SDATPos])
            retString += tempString
            SDATPos += 1
        elif listItem == SHORT:
            tempString = str(read_short(SDATPos))
            retString += tempString
            SDATPos += 2
        elif listItem == LONG:
            tempString = str(read_long(SDATPos))
            retString += tempString
            SDATPos += 4
        elif listItem == FILE: #point to the file name
            tempID = read_short(SDATPos)
            matchID = 0
            done = False
            while matchID < len(fileNameID) and not done:
                if fileNameID[matchID] == tempID:
                    done = True
                else:
                    matchID += 1
            retString += names[FILE][matchID] + itemExt[fileType[matchID]]
            SDATPos += 2
        else: #point to the name of the item
            if read_short(SDATPos) < len(names[listItem]):
                retString += names[listItem][read_short(SDATPos)]
            else:
                if read_short(SDATPos) == 65535 and listItem == WAVARC: #unused wavarc slot
                    retString += "NULL"
                else:
                    retString += itemString[listItem] + "_" + str(read_short(SDATPos))
            SDATPos += 2
            if listItem == PLAYER:
                SDATPos -= 1
    return retString

def convert_params(tArray,tList):
    retList = []
    retList.append(tArray[0])
    for i, listItem in enumerate(tList):
        if listItem <= BYTE: #convert to integer
            retList.append(int(tArray[i + 1]))
        elif listItem == FILE and optimize: #check file MD5 for duplicates
            matchID = 0
            done = False
            while matchID < len(fileAll) and not done:
                if fileAll[matchID] == tArray[i + 1]:
                    done = True
                else:
                    matchID += 1
            tempMD5 = fileAllMD5[matchID]
            matchID2 = 0
            done = False
            while matchID2 < len(fileMD5) and not done:
                if fileMD5[matchID2] == tempMD5:
                    done = True
                else:
                    matchID2 += 1
            retList.append(matchID2)
        else: #reference item by string
            matchID = 0
            done = False
            if tArray[i + 1] == "NULL" and listItem == WAVARC: #unused bank
                done = True
                matchID = 65535
            while matchID < len(names[listItem]) and not done:
                if names[listItem][matchID] == tArray[i + 1]:
                    done = True
                else:
                    matchID += 1
            retList.append(matchID)
    return retList

def append_list(tList): #append a list of bytes to SDAT
    for i, listItem in enumerate(tList):
        SDAT.append(listItem)

def append_reserve(x): #append a number of 0x00 bytes to SDAT
    for i in range(x):
        SDAT.append(0)

def append_params(item,index,tList): #append paramerters of an item to SDAT
    for i, listItem in enumerate(tList):
        if listItem in (BYTE, PLAYER): #parameter is an 8-bit write
            append_byte(itemData[item][index + i + 1])
        elif listItem == LONG: #parameter is a 32-bit write
            append_long(itemData[item][index + i + 1])
        else: #parameter is a 16-bit write
            append_short(itemData[item][index + i + 1])

def append_long(x): #append a 32bit value to SDAT LSB first
    SDAT.append((x & 0xFF))
    x = x >> 8
    SDAT.append((x & 0xFF))
    x = x >> 8
    SDAT.append((x & 0xFF))
    x = x >> 8
    SDAT.append((x & 0xFF))

def append_short(x): #append a 16bit value to SDAT LSB first
    SDAT.append((x & 0xFF))
    x = x >> 8
    SDAT.append((x & 0xFF))

def append_byte(x): #append an 8bit value to SDAT
    SDAT.append((x & 0xFF))

def write_long(loc, x): #write a 32bit value to SDAT at position loc LSB first
    SDAT[loc] = (x & 0xFF)
    x = x >> 8
    SDAT[loc+1] = (x & 0xFF)
    x = x >> 8
    SDAT[loc+2] = (x & 0xFF)
    x = x >> 8
    SDAT[loc+3] = (x & 0xFF)

def write_short(loc, x): #write a 16bit value to SDAT at position loc LSB first
    SDAT[loc] = (x & 0xFF)
    x = x >> 8
    SDAT[loc+1] = (x & 0xFF)

def write_byte(loc, x): #write an 8bit value to SDAT at position loc
    SDAT[loc] = (x & 0xFF)

def get_string():
    global SDATPos
    retString = ""
    if SDATPos <= 0x40:
        return "NULL"
    i = SDAT[SDATPos]
    SDATPos += 1
    while i > 0:
        retString += chr(i)
        i = SDAT[SDATPos]
        SDATPos += 1
    return retString

#Main
print("SDAT-Tool " + version)
infileArg = -1;
outfileArg = -1;
for i, argument in enumerate(sysargv):
    if i > 0:
        if argument.startswith("-"):
            if argument in ("-u", "--unpack"):
                mode = 1
            elif argument in ("-b", "--build"):
                mode = 2
            elif argument in ("-h", "--help"):
                mode = 0
            elif argument in ("-m", "--md5"):
                calcMD5 = True
            elif argument in ("-o", "--optimize"):
                optimize = True
                skipFileOrder = True
            elif argument in ("-ru", "--removeUnused"):
                optimize = True
                skipFileOrder = True
                removeUnused = True
            elif argument in ("-ns", "--noSymbBlock"):
                skipSymbBlock = True
        else:
            if infileArg == -1: infileArg=i
            elif outfileArg == -1: outfileArg=i

if infileArg == -1:
    mode = 0
else:
    if outfileArg == -1:
        if sysargv[infileArg].find(".sdat") != -1:
            if mode == 0: mode = 1
            outfileArg=len(sysargv)
            sysargv.append(sysargv[infileArg].replace(".sdat",""))
        else:
            mode = 0
    else:
        if sysargv[infileArg]==sysargv[outfileArg]:
            print("Input and output files cannot be the same")
            sys.exit()
if mode == 0: #Help
    print("Usage: "+sysargv[0]+" [SDAT File] [mode] [SDAT Folder] [flags]\nMode:\n        -b        Build SDAT\n        -u        Unpack SDAT\n        -h        Show this help message\n\nFlags:\n        -m        Calculate file MD5 when unpacking\n        -o        Build Optimized\n        -ru        Build without unused entries (can break games)\n        -ns        Build without a SymbBlock\n")
    sys.exit()

if mode == 1: #Unpack
    print("Unpacking...")
    if not os.path.exists(sysargv[outfileArg]):
        os.makedirs(sysargv[outfileArg])
    with open(sysargv[infileArg], "rb") as infile:
         SDAT = infile.read()
    fileSize = len(SDAT)
    SDATSize = read_long(8)
    headerSize = read_short(12)
    blocks = read_short(14)
    SDATPos = 16
    if blocks == 4:
        symbOffset = read_long(SDATPos)
        symbSize = read_long(SDATPos + 4)
        SDATPos += 8
    infoOffset = read_long(SDATPos)
    infoSize = read_long(SDATPos + 4)
    SDATPos += 8
    fatOffset = read_long(SDATPos)
    fatSize = read_long(SDATPos + 4)
    SDATPos += 8
    fileOffset = read_long(SDATPos)
    fileSize = read_long(SDATPos + 4)

    #Symb Block
    if blocks == 4:
        SDATPos = symbOffset + 8
        for i in range(8):
            itemSymbOffset[i] = read_long(SDATPos + (i * 4)) + symbOffset
        for i in range(8):
            if i != SEQARC:
                SDATPos = itemSymbOffset[i]
                entries = read_long(SDATPos)
                for ii in range(entries):
                    SDATPos = read_long(itemSymbOffset[i] + 4 + (ii * 4)) + symbOffset
                    names[i].append(get_string())
            else:
                SDATPos = itemSymbOffset[i]
                entries = read_long(SDATPos)
                if entries > 0:
                    outfile = open(sysargv[outfileArg] + "/SymbBlock.txt","w")
                    outfile.write(itemString[i] + "{\n")
                for ii in range(entries):
                    SDATPos = read_long(itemSymbOffset[i] + 4 + (ii * 8)) + symbOffset
                    names[i].append(get_string())
                    if entries > 0:
                        outfile.write(names[i][len(names[i]) - 1] + "\n")
                    SDATPos = read_long(itemSymbOffset[i] + 8 + (ii * 8)) + symbOffset
                    SEQARCSubOffset = SDATPos
                    count = read_long(SDATPos)
                    for x in range(count):
                        SDATPos = read_long(SEQARCSubOffset + 4 + (x * 4)) + symbOffset
                        if entries > 0:
                            outfile.write("\t" + get_string() + "\n")
                if entries > 0:
                    outfile.write("}\n")
                    outfile.close()

    #Info Block
    SDATPos = infoOffset + 8
    for i in range(8):
        itemOffset[i] = read_long(SDATPos + (i * 4)) + infoOffset
    with open(sysargv[outfileArg] + "/InfoBlock.txt","w") as outfile:
        for i in range(8):
            SDATPos = itemOffset[i]
            outfile.write(itemParamString[i])
            entries = read_long(SDATPos)
            for ii in range(entries):
                SDATPos = read_long(itemOffset[i] + 4 + (ii * 4)) + infoOffset
                if SDATPos - infoOffset > 0x40:
                    count = read_long(SDATPos) #count is only used for group
                    if blocks == 4 and ii < len(names[i]):
                        iName = names[i][ii]
                    else:
                        iName = itemString[i] + "_" + str(ii)
                    if i in (SEQ, SEQARC, BANK, WAVARC, STRM): #These have files
                        fileType.append(i)
                        fileNameID.append(read_short(SDATPos))
                        names[FILE].append(iName)
                    outfile.write(iName + "," + get_params(itemParams[i]))
                    if i == GROUP:
                        for x in range(count):
                            outfile.write("," + get_params([LONG,LONG]))
                    outfile.write("\n")
                else:
                    outfile.write("NULL\n")
            outfile.write("}\n\n")

    #FAT Block / File Block
    SDATPos = fatOffset + 8
    entries = read_long(SDATPos)
    with open(sysargv[outfileArg] + "/FileID.txt","w") as IDFile:
        if not os.path.exists(sysargv[outfileArg] + "/Files"):
            os.makedirs(sysargv[outfileArg] + "/Files")
        if not os.path.exists(sysargv[outfileArg] + "/Files/" + itemString[0]):
            os.makedirs(sysargv[outfileArg] + "/Files/" + itemString[0])
        if not os.path.exists(sysargv[outfileArg] + "/Files/" + itemString[1]):
            os.makedirs(sysargv[outfileArg] + "/Files/" + itemString[1])
        if not os.path.exists(sysargv[outfileArg] + "/Files/" + itemString[2]):
            os.makedirs(sysargv[outfileArg] + "/Files/" + itemString[2])
        if not os.path.exists(sysargv[outfileArg] + "/Files/" + itemString[3]):
            os.makedirs(sysargv[outfileArg] + "/Files/" + itemString[3])
        if not os.path.exists(sysargv[outfileArg] + "/Files/" + itemString[7]):
            os.makedirs(sysargv[outfileArg] + "/Files/" + itemString[7])
        for i in range(entries):
            SDATPos = read_long(fatOffset + 12 + (i * 16))
            tempSize = read_long(fatOffset + 16 + (i * 16))
            done = False
            fileRefID = 0
            fileHeader = str(SDAT[SDATPos:SDATPos+4])[2:6]
            if fileHeader in itemHeader:
                tempPath = sysargv[outfileArg] + "/Files/" + itemString[itemHeader.index(fileHeader)] + "/" + "unknown_" + hex(i).lstrip("0x").rstrip("L").zfill(2).upper()
                tempName = "unknown_" + hex(i).lstrip("0x").rstrip("L").zfill(2).upper()
                tempExt = itemExt[itemHeader.index(fileHeader)]
            else:
                tempPath = sysargv[outfileArg] + "/Files/unknown_" + hex(i).lstrip("0x").rstrip("L").zfill(2).upper()
                tempName = "unknown_" + hex(i).lstrip("0x").rstrip("L").zfill(2).upper()
                tempExt = ""
            while fileNameID[fileRefID] != i and not done:
                fileRefID += 1
                if fileRefID >= len(fileNameID):
                    fileRefID = -1
                    done = True
            if fileRefID != -1:
                tempPath = sysargv[outfileArg] + "/Files/" + itemString[fileType[fileRefID]] + "/" + names[FILE][fileRefID]
                tempName = names[FILE][fileRefID]
            if fileHeader == "SWAR":
                numSwav = read_long(SDATPos + 0x38)
                if not os.path.exists(tempPath):
                    os.makedirs(tempPath)
                with open(tempPath + "/FileID.txt","w") as swavIDFile:
                    for ii in range(numSwav):
                        swavOffset = SDATPos + read_long(SDATPos + (ii * 4) + 0x3C)
                        swavLength = SDATPos + read_long(SDATPos + ((ii + 1) * 4) + 0x3C)
                        if ii + 1 == numSwav:
                            swavLength = SDATPos+tempSize
                        swavSize = swavLength - swavOffset
                        with open(tempPath + "/" + hex(ii).lstrip("0x").rstrip("L").zfill(2).upper() + ".swav","wb") as outfile:
                            outfile.write(b'SWAV') #Header
                            outfile.write(b'\xFF\xFE\x00\x01') #magic
                            outfile.write((swavSize + 0x18).to_bytes(4,byteorder='little'))
                            outfile.write(b'\x10\x00\x01\x00') #structure size and blocks
                            outfile.write(b'DATA')
                            outfile.write((swavSize + 0x08).to_bytes(4,byteorder='little'))
                            outfile.write(SDAT[swavOffset:swavLength])
                        swavIDFile.write(hex(ii).lstrip("0x").rstrip("L").zfill(2).upper() + ".swav\n")
            elif fileHeader == "SBNK":
                numInst = read_long(SDATPos + 0x38)
                sbnkEnd = read_long(SDATPos + 0x08) + SDATPos
                with open(tempPath + ".txt","w") as sbnkIDFile:
                    instType = []
                    instOffset = []
                    instOrder = []
                    instUsed = []
                    lastPointer = -1 #Because some instruments will point to the same exact definition
                    furthestRead = SDATPos + 0x3C + (numInst * 4) #Because someone decided to leave in data that's not pointed to...
                    for ii in range(numInst):
                        instType.append(SDAT[SDATPos + 0x3C + (ii * 4)])
                        instOffset.append(read_short(SDATPos + 0x3C + (ii * 4) + 1))
                        instOrder.append(-1)
                        instUsed.append(False)
                    for ii in range(numInst): #get the order the data is stored for 1:1 builds
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
                            sbnkIDFile.write(",SameAsAbove\n")
                        elif instType[instOrder[ii]] == 0:
                            sbnkIDFile.write(str(instOrder[ii]))
                            sbnkIDFile.write(",NULL\n")
                        elif instType[instOrder[ii]] < 16:
                            if furthestRead < SDATPos + instOffset[instOrder[ii]]:
                                sbnkIDFile.write("Unused")
                                while furthestRead < SDATPos + instOffset[instOrder[ii]]:
                                    sbnkIDFile.write("," + str(SDAT[furthestRead]))
                                    furthestRead += 1
                                sbnkIDFile.write("\n")
                            sbnkIDFile.write(str(instOrder[ii]))
                            if instType[instOrder[ii]] == 1:
                                sbnkIDFile.write(",Single")
                            elif instType[instOrder[ii]] == 2:
                                sbnkIDFile.write(",PSG1")
                            elif instType[instOrder[ii]] == 3:
                                sbnkIDFile.write(",PSG2")
                            elif instType[instOrder[ii]] == 4:
                                sbnkIDFile.write(",PSG3")
                            else:
                                sbnkIDFile.write("," + str(instType[instOrder[ii]]))
                            sbnkIDFile.write("," + str(read_short(SDATPos + instOffset[instOrder[ii]])))
                            sbnkIDFile.write("," + str(read_short(SDATPos + instOffset[instOrder[ii]] + 2)))
                            sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 4]))
                            sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 5]))
                            sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 6]))
                            sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 7]))
                            sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 8]))
                            sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 9]) + "\n")
                            if SDATPos + instOffset[instOrder[ii]] + 9 > furthestRead:
                                furthestRead = SDATPos + instOffset[instOrder[ii]] + 10
                        elif instType[instOrder[ii]] == 16:
                            if furthestRead < SDATPos + instOffset[instOrder[ii]]:
                                sbnkIDFile.write("Unused")
                                while furthestRead < SDATPos + instOffset[instOrder[ii]]:
                                    sbnkIDFile.write("," + str(SDAT[furthestRead]))
                                    furthestRead += 1
                                sbnkIDFile.write("\n")
                            sbnkIDFile.write(str(instOrder[ii]))
                            lowNote = SDAT[SDATPos + instOffset[instOrder[ii]]]
                            highNote = SDAT[SDATPos + instOffset[instOrder[ii]] + 1]
                            sbnkIDFile.write(",Drums")
                            sbnkIDFile.write("," + str(lowNote))
                            sbnkIDFile.write("," + str(highNote) + "\n")
                            x = 0
                            while read_short(SDATPos + instOffset[instOrder[ii]] + 2 + (x * 12)) == 1 and read_short(SDATPos + instOffset[instOrder[ii]] + 6 + (x * 12)) < 4:
                                sbnkIDFile.write("\t" + str(read_short(SDATPos + instOffset[instOrder[ii]] + 2 + (x * 12))))
                                sbnkIDFile.write("," + str(read_short(SDATPos + instOffset[instOrder[ii]] + 4 + (x * 12))))
                                sbnkIDFile.write("," + str(read_short(SDATPos + instOffset[instOrder[ii]] + 6 + (x * 12))))
                                sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 8 + (x * 12)]))
                                sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 9 + (x * 12)]))
                                sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 10 + (x * 12)]))
                                sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 11 + (x * 12)]))
                                sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 12 + (x * 12)]))
                                sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 13 + (x * 12)]) + "\n")
                                x += 1
                            x -= 1
                            if SDATPos + instOffset[instOrder[ii]] + 13 + (x * 12) > furthestRead:
                                furthestRead = SDATPos + instOffset[instOrder[ii]] + 14 + (x * 12)
                        elif instType[instOrder[ii]] == 17:
                            if furthestRead < SDATPos + instOffset[instOrder[ii]]:
                                sbnkIDFile.write("Unused")
                                while furthestRead < SDATPos + instOffset[instOrder[ii]]:
                                    sbnkIDFile.write("," + str(SDAT[furthestRead]))
                                    furthestRead += 1
                                sbnkIDFile.write("\n")
                            sbnkIDFile.write(str(instOrder[ii]))
                            regions = 0
                            sbnkIDFile.write(",Keysplit")
                            for x in range(8):
                                if SDAT[SDATPos + instOffset[instOrder[ii]] + x] > 0:
                                    regions += 1
                                sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + x]))
                            sbnkIDFile.write("\n")
                            tempOffset = SDATPos + instOffset[instOrder[ii]] + 8
                            for x in range(regions):
                                sbnkIDFile.write("\t" + str(read_short(SDATPos + instOffset[instOrder[ii]] + 8 + (x * 12))))
                                sbnkIDFile.write("," + str(read_short(SDATPos + instOffset[instOrder[ii]] + 10 + (x * 12))))
                                sbnkIDFile.write("," + str(read_short(SDATPos + instOffset[instOrder[ii]] + 12 + (x * 12))))
                                sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 14 + (x * 12)]))
                                sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 15 + (x * 12)]))
                                sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 16 + (x * 12)]))
                                sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 17 + (x * 12)]))
                                sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 18 + (x * 12)]))
                                sbnkIDFile.write("," + str(SDAT[SDATPos + instOffset[instOrder[ii]] + 19 + (x * 12)]) + "\n")
                                if SDATPos + instOffset[instOrder[ii]] + 19 + (x * 12) > furthestRead:
                                    furthestRead = SDATPos + instOffset[instOrder[ii]] + 20 + (x * 12)
                        lastPointer = instOffset[instOrder[ii]]
                    if furthestRead < sbnkEnd:
                        sbnkIDFile.write("Unused")
                        while furthestRead < sbnkEnd:
                            sbnkIDFile.write("," + str(SDAT[furthestRead]))
                            furthestRead += 1
                        sbnkIDFile.write("\n")
            with open(tempPath + tempExt,"wb") as outfile:
                outfile.write(SDAT[SDATPos:SDATPos+tempSize])
            tempFileString = SDAT[SDATPos:SDATPos+tempSize]
            IDFile.write(tempName + tempExt)
            if calcMD5:
                thisMD5 = hashlib.md5(tempFileString)
                IDFile.write(";MD5 = " + thisMD5.hexdigest())
            IDFile.write("\n")
    ts2 = time.time() - ts
    print("Done: " + str(ts2) + "s")

if mode == 2: #Build
    print("Building...")
    blocks = 4
    if skipSymbBlock:
        blocks = 3
    if not os.path.exists(sysargv[outfileArg] + "/FileID.txt"):
        print("\nMissing FileID.txt, files will be ordered as they are in the InfoBlock.\n")
        skipFileOrder = True
    if not os.path.exists(sysargv[outfileArg] + "/InfoBlock.txt"):
        print("\nMissing InfoBlock.txt\n")
        quit()

    if not skipFileOrder:
        with open(sysargv[outfileArg] + "/FileID.txt", "r") as IDFile:
            done = False
            while not done:
                thisLine = IDFile.readline()
                if not thisLine:
                    done = True
                thisLine = thisLine.split(";") #ignore anything commented out
                thisLine = thisLine[0]
                thisLine = thisLine.split("\n") #remove newline
                thisLine = thisLine[0]
                if thisLine != "":
                    names[FILE].append(thisLine)
                    itemCount[FILE] += 1
    with open(sysargv[outfileArg] + "/InfoBlock.txt", "r") as infoFile:
        seqarcSymbSubCount = [] #keep track of how many sub strings are in each seqarc
        for i in range(8):
            done = False
            while not done:
                thisLine = infoFile.readline()
                if not thisLine:
                    done = True
                thisLine = thisLine.split(";") #ignore anything commented out
                thisLine = thisLine[0]
                thisLine = thisLine.split("\n") #remove newline
                thisLine = thisLine[0]
                if thisLine.find("{") == -1: #ignore lines with {
                    if thisLine.find("}") != -1: #end of section
                        done = True
                    elif thisLine != "":
                        thisLine = thisLine.split(",") #split parameters
                        if check_unused(removeUnused, i, thisLine[0]):
                            names[i].append(thisLine[0])
                            if i == SEQARC:
                                seqarcSymbSubCount.append(0)
                            if thisLine[0] != "NULL":
                                if skipFileOrder and itemParams[i][0] == FILE:
                                    add_fileName(thisLine[1])
                                for ii, param in enumerate(itemParams[i]):
                                    if param >= 0:
                                        namesUsed[param].append(thisLine[ii + 1])
    if blocks == 4 and os.path.exists(sysargv[outfileArg] + "/SymbBlock.txt"):
        with open(sysargv[outfileArg] + "/SymbBlock.txt", "r") as symbFile:
            thisLine = ""
            seqarcSymbSubNum = 0
            done = False
            seqarcSymbSubParent = []
            seqarcSymbSubName = []
            mainSEQARCID = -1
            while not done:
                thisLine = symbFile.readline()
                if not thisLine:
                    done = True
                thisLine = thisLine.split(";") #ignore anything commented out
                thisLine = thisLine[0]
                thisLine = thisLine.split("\n") #remove newline
                thisLine = thisLine[0]
                if thisLine.find("{") == -1: #ignore lines with {
                    if thisLine.find("}") != -1: #end of section
                        done = True
                    elif thisLine != "":
                        if thisLine[:1] == "\t": #is a sub string
                            if mainSEQARCID != -1:
                                seqarcSymbSubName.append(thisLine[1:])
                                seqarcSymbSubParent.append(mainSEQARCID)
                                seqarcSymbSubNum += 1
                        else: #not a sub string
                            tempID = 0
                            done2 = False
                            while tempID < len(names[SEQARC]) and not done2:
                                if names[SEQARC][tempID] == thisLine:
                                    done2 = True
                                else:
                                    tempID += 1
                            if done2:
                                if mainSEQARCID != -1:
                                    seqarcSymbSubCount[mainSEQARCID] = seqarcSymbSubNum
                                mainSEQARCID = tempID
                                seqarcSymbSubNum = 0
                            else:
                                mainSEQARCID = -1
            if mainSEQARCID != -1:
                seqarcSymbSubCount[mainSEQARCID] = seqarcSymbSubNum
    with open(sysargv[outfileArg] + "/InfoBlock.txt", "r") as infoFile:
        for i in range(8):
            done = False
            params = len(itemParams[i]) + 1
            while not done:
                thisLine = infoFile.readline()
                if not thisLine:
                    done = True
                thisLine = thisLine.split(";") #ignore anything commented out
                thisLine = thisLine[0]
                thisLine = thisLine.split("\n") #remove newline
                thisLine = thisLine[0]
                if thisLine.find("{") == -1: #ignore lines with {
                    if thisLine.find("}") != -1: #end of section
                        done = True
                    elif thisLine != "":
                        thisLine = thisLine.split(",") #split parameters
                        if check_unused(removeUnused, i, thisLine[0]):
                            if thisLine[0] == "NULL":
                                itemData[i].append("NULL")
                                for ii in range(params - 1):
                                    itemData[i].append(0)
                                itemCount[i] += 1
                            else:
                                if i == GROUP:
                                    params = (int(thisLine[1]) * 2) + 2
                                    for ii, number in enumerate(thisLine[1:]):
                                        thisLine[ii + 1] = int(number) #convert ID to an integer
                                if len(thisLine) != params:
                                    print("\n" + itemString[i] + " wrong number of parameters.\n")
                                    quit()
                                if i != GROUP:
                                    thisLine = convert_params(thisLine,itemParams[i])
                                for ii in range(params):
                                    itemData[i].append(thisLine[ii])
                                itemCount[i] += 1
    append_list([ord('S'),ord('D'),ord('A'),ord('T')]) #Header
    append_list([0xFF,0xFE,0x00,0x01]) #Magic
    append_reserve(4) #File size
    append_short((blocks + 4) * 8) #Header size
    append_short(blocks) #Blocks
    append_reserve((blocks + 2) * 8) #reserve space for the offsets and sizes
    headeri = 0 #help point back to the block offsets and sizes when ready to write

    if blocks == 4: #symbBlock
        symbBlockOffset = len(SDAT)
        append_list([ord('S'),ord('Y'),ord('M'),ord('B')]) #Header
        append_reserve(4) #symbBlock size
        append_reserve(8 * 4) #reserve space for the offsets
        append_reserve(24) #reserved bytes

        for i in range(8):
            if i != SEQARC:
                itemSymbOffset[i] = len(SDAT)
                write_long(symbBlockOffset + (i * 4) + 8, itemSymbOffset[i] - symbBlockOffset)
                append_long(itemCount[i])
                append_reserve(itemCount[i] * 4)
            else:
                itemSymbOffset[i] = len(SDAT)
                seqarcSymbSubOffset = []
                write_long(symbBlockOffset + (i * 4) + 8, itemSymbOffset[i] - symbBlockOffset)
                append_long(itemCount[i])
                append_reserve(itemCount[i] * 8) #this has sub-groups
                for ii in range(itemCount[i]):
                    write_long((itemSymbOffset[i] + 8) + (ii * 8), len(SDAT) - symbBlockOffset)
                    seqarcSymbSubOffset.append(len(SDAT))
                    append_long(seqarcSymbSubCount[ii])
                    append_reserve(seqarcSymbSubCount[ii] * 4)

        for i in range(8):
            if i != SEQARC:
                for ii in range(itemCount[i]):
                    if names[i][ii] != "NULL":
                        write_long((itemSymbOffset[i] + 4) + (ii * 4), len(SDAT) - symbBlockOffset)
                        for x, character in enumerate(names[i][ii]):
                            append_byte(ord(character))
                        append_byte(0) #terminate string
            else:
                for ii in range(itemCount[i]):
                    if names[i][ii] != "NULL":
                        write_long((itemSymbOffset[i] + 4) + (ii * 8), len(SDAT) - symbBlockOffset)
                        for x, character in enumerate(names[i][ii]):
                            append_byte(ord(character))
                        append_byte(0) #terminate string
                        curSeqarcSub = 0
                        for subi, name in enumerate(seqarcSymbSubName):
                            if seqarcSymbSubParent[subi] == ii:
                                if name != "NULL":
                                    write_long((seqarcSymbSubOffset[ii] + 4) + (curSeqarcSub * 4), len(SDAT) - symbBlockOffset)
                                    for x, character in enumerate(name):
                                        append_byte(ord(character))
                                    append_byte(0) #terminate string
                                curSeqarcSub += 1

        write_long(16, symbBlockOffset)
        write_long(20, len(SDAT) - symbBlockOffset)
        headeri += 1
        while (len(SDAT) & 0xFFFFFFFC) != len(SDAT):
            append_reserve(1) #pad to the nearest 0x04 byte alignment
        write_long(symbBlockOffset + 4, len(SDAT) - symbBlockOffset)

    infoBlockOffset = len(SDAT) #infoBlock
    append_list([ord('I'),ord('N'),ord('F'),ord('O')]) #Header
    append_reserve(4) #File size
    append_reserve(8 * 4) #reserve space for the offsets
    append_reserve(24) #reserved bytes

    for i in range(8):
        itemOffset[i] = len(SDAT)
        write_long(infoBlockOffset + (i * 4) + 8, itemOffset[i] - infoBlockOffset)
        append_long(itemCount[i])
        append_reserve(itemCount[i] * 4)
        if i != GROUP:
            params = len(itemParams[i]) + 1
            for ii in range(itemCount[i]):
                if itemData[i][(ii * params)] != "NULL":
                    write_long((itemOffset[i] + 4) + (ii * 4), len(SDAT) - infoBlockOffset)
                    append_params(i,(ii * params),itemParams[i])
        else:
            ii = 0
            entry = 0
            while ii < len(itemData[i]):
                if itemData[i][ii] != "NULL":
                    write_long((itemOffset[i] + 4) + (entry * 4), len(SDAT) - infoBlockOffset)
                    ii += 1 #skip the name
                    append_long(itemData[i][ii])
                    count = itemData[i][ii]
                    ii += 1
                    for x in range(count):
                        append_long(itemData[i][ii])
                        ii += 1
                        append_long(itemData[i][ii])
                        ii += 1
                else:
                    ii += 2 #skip name and 0 for number of entries
                entry += 1
    write_long(16 + (headeri * 8), infoBlockOffset)
    write_long(20 + (headeri * 8), len(SDAT) - infoBlockOffset)
    headeri += 1
    while (len(SDAT) & 0xFFFFFFFC) != len(SDAT):
        append_reserve(1) #pad to the nearest 0x04 byte alignment
    write_long(infoBlockOffset + 4, len(SDAT) - infoBlockOffset)

    fatBlockOffset = len(SDAT) #fatBlock
    append_list([ord('F'),ord('A'),ord('T'),0x20]) #Header
    append_long((itemCount[FILE] * 16) + 12) #fatBlock size
    append_long(itemCount[FILE]) #number of FAT records
    append_reserve((itemCount[FILE] * 16))

    write_long(16 + (headeri * 8), fatBlockOffset)
    write_long(20 + (headeri * 8), len(SDAT) - fatBlockOffset)
    headeri += 1
    while (len(SDAT) & 0xFFFFFFFC) != len(SDAT):
        append_reserve(1) #pad to the nearest 0x04 byte alignment
    write_long(fatBlockOffset + 4, len(SDAT) - fatBlockOffset)

    fileBlockOffset = len(SDAT) #fileBlock
    append_list([ord('F'),ord('I'),ord('L'),ord('E')]) #Header
    append_reserve(4) #fileBlock size
    append_long(itemCount[FILE]) #number of files
    append_reserve(4) #reserved
    while (len(SDAT) & 0xFFFFFFE0) != len(SDAT):
        append_reserve(1) #pad to the nearest 0x20 byte alignment

    curFile = 0
    tFileBuffer = []
    for i, fName in enumerate(names[FILE]):
        testPath = sysargv[outfileArg] + "/Files/" + itemString[itemExt.index(fName[-5:])] + "/" + fName
        if not os.path.exists(testPath):
            testPath = sysargv[outfileArg] + "/Files/" + fName
            if not os.path.exists(testPath):
                if fName[-5:] == ".swar":#can the swar be built?
                    testPath = sysargv[outfileArg] + "/Files/" + itemString[3] + "/" + fName[:-5] + "/FileID.txt"
                    if not os.path.exists(testPath):
                        print("\nMissing File:" + testPath)
                        quit()
                    with open(testPath, "r") as swavIDFile:
                        done = False
                        swavName = []
                        while not done:
                            thisLine = swavIDFile.readline()
                            if not thisLine:
                                done = True
                            thisLine = thisLine.split(";") #ignore anything commented out
                            thisLine = thisLine[0]
                            thisLine = thisLine.split("\n") #remove newline
                            thisLine = thisLine[0]
                            if thisLine != "":
                                swavName.append(thisLine)
                    swarTemp = []
                    for ii, sName in enumerate(swavName):
                        testPath = sysargv[outfileArg] + "/Files/" + itemString[3] + "/" + fName[:-5] + "/" + sName
                        if not os.path.exists(testPath):
                            print("\nMissing File:" + testPath)
                            quit()
                        with open(testPath, "rb") as tempFile:
                            swarTemp.append(tempFile.read())
                    testPath = sysargv[outfileArg] + "/Files/" + itemString[3] + "/" + fName
                    with open(testPath, "wb") as swarFile:
                        swarSize = sum(len(sf[0x18:]) for sf in swarTemp)
                        swarFile.write(b'SWAR') #Header
                        swarFile.write(b'\xFF\xFE\x00\x01') #magic
                        swarFile.write((swarSize + 0x3C + (len(swarTemp) * 4)).to_bytes(4,byteorder='little'))
                        swarFile.write(b'\x10\x00\x01\x00') #structure size and blocks
                        swarFile.write(b'DATA')
                        swarFile.write((swarSize + 0x2C + (len(swarTemp) * 4)).to_bytes(4,byteorder='little'))
                        swarFile.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00') #reserved
                        swarFile.write((len(swarTemp)).to_bytes(4,byteorder='little'))
                        swarPointer = 0x3C + (len(swarTemp) * 4) #where the first swav will be in the file
                        for ii, sFile in enumerate(swarTemp):
                            swarFile.write((swarPointer).to_bytes(4,byteorder='little'))
                            swarPointer += len(sFile[0x18:])
                        for ii, sFile in enumerate(swarTemp):
                            swarFile.write(sFile[0x18:])
                elif fName[-5:] == ".sbnk":#can the sbnk be built?
                    testPath = sysargv[outfileArg] + "/Files/" + itemString[2] + "/" + fName[:-5] + ".txt"
                    if not os.path.exists(testPath):
                        print("\nMissing File:" + testPath)
                        quit()
                    with open(testPath, "r") as sbnkIDFile:
                        done = False
                        sbnkLines = []
                        numInst = 0
                        while not done:
                            thisLine = sbnkIDFile.readline()
                            if not thisLine:
                                done = True
                            thisLine = thisLine.split(";") #ignore anything commented out
                            thisLine = thisLine[0]
                            thisLine = thisLine.split("\n") #remove newline
                            thisLine = thisLine[0]
                            if thisLine != "":
                                sbnkLines.append(thisLine)
                                if thisLine.find("\t") == -1 and thisLine.find("Unused") == -1: #Don't count unused or sub definitions
                                    numInst += 1
                    sbnkHeader = []
                    sbnkData = []
                    prevPointer = b'\x00\x00\x00\x00'
                    sbnkHeader.append(b'SBNK') #Header
                    sbnkHeader.append(b'\xFF\xFE\x00\x01') #magic
                    sbnkHeader.append(b'\x00\x00\x00\x00') #Reserve for sbnk size
                    sbnkHeader.append(b'\x10\x00\x01\x00') #structure size and blocks
                    sbnkHeader.append(b'DATA')
                    sbnkHeader.append(b'\x00\x00\x00\x00') #Reserve for struct size
                    sbnkHeader.append(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00') #reserved
                    sbnkHeader.append((numInst).to_bytes(4,byteorder='little')) #Number of instruments
                    for ii in range(numInst):
                        sbnkHeader.append(b'\x00\x00\x00\x00') #Reserve for pointers
                    for ii, inst in enumerate(sbnkLines):
                        thisLine = inst
                        if thisLine.find("\t") == -1:
                            thisLine = thisLine.split(",")
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
                                        sbnkData.append((int(unusedData)).to_bytes(1,byteorder='little'))
                                else:
                                    prevPointer = (int(thisLine[1]) + ((sbnkHeaderSize + sum(len(tf) for tf in sbnkData)) << 8)).to_bytes(4,byteorder='little')
                                    sbnkHeader[8 + int(thisLine[0])] = prevPointer
                                if int(thisLine[1]) < 16:
                                    sbnkData.append((int(thisLine[2])).to_bytes(2,byteorder='little'))
                                    sbnkData.append((int(thisLine[3])).to_bytes(2,byteorder='little'))
                                    sbnkData.append((int(thisLine[4])).to_bytes(1,byteorder='little'))
                                    sbnkData.append((int(thisLine[5])).to_bytes(1,byteorder='little'))
                                    sbnkData.append((int(thisLine[6])).to_bytes(1,byteorder='little'))
                                    sbnkData.append((int(thisLine[7])).to_bytes(1,byteorder='little'))
                                    sbnkData.append((int(thisLine[8])).to_bytes(1,byteorder='little'))
                                    sbnkData.append((int(thisLine[9])).to_bytes(1,byteorder='little'))
                                elif int(thisLine[1]) == 16:
                                    sbnkData.append((int(thisLine[2])).to_bytes(1,byteorder='little'))
                                    sbnkData.append((int(thisLine[3])).to_bytes(1,byteorder='little'))
                                elif int(thisLine[1]) == 17:
                                    sbnkData.append((int(thisLine[2])).to_bytes(1,byteorder='little'))
                                    sbnkData.append((int(thisLine[3])).to_bytes(1,byteorder='little'))
                                    sbnkData.append((int(thisLine[4])).to_bytes(1,byteorder='little'))
                                    sbnkData.append((int(thisLine[5])).to_bytes(1,byteorder='little'))
                                    sbnkData.append((int(thisLine[6])).to_bytes(1,byteorder='little'))
                                    sbnkData.append((int(thisLine[7])).to_bytes(1,byteorder='little'))
                                    sbnkData.append((int(thisLine[8])).to_bytes(1,byteorder='little'))
                                    sbnkData.append((int(thisLine[9])).to_bytes(1,byteorder='little'))
                        else:
                            thisLine = thisLine.split("\t")
                            thisLine = thisLine[1]
                            thisLine = thisLine.split(",")
                            sbnkData.append((int(thisLine[0])).to_bytes(2,byteorder='little'))
                            sbnkData.append((int(thisLine[1])).to_bytes(2,byteorder='little'))
                            sbnkData.append((int(thisLine[2])).to_bytes(2,byteorder='little'))
                            sbnkData.append((int(thisLine[3])).to_bytes(1,byteorder='little'))
                            sbnkData.append((int(thisLine[4])).to_bytes(1,byteorder='little'))
                            sbnkData.append((int(thisLine[5])).to_bytes(1,byteorder='little'))
                            sbnkData.append((int(thisLine[6])).to_bytes(1,byteorder='little'))
                            sbnkData.append((int(thisLine[7])).to_bytes(1,byteorder='little'))
                            sbnkData.append((int(thisLine[8])).to_bytes(1,byteorder='little'))
                    sbnkSize = sum(len(tf) for tf in sbnkData) + sbnkHeaderSize
                    while (sbnkSize & 0xFFFFFFFC) != sbnkSize:
                        sbnkData.append(b'\x00') #pad to the nearest 0x4 byte alignment
                        sbnkSize += 1
                    sbnkHeader[2] = (sbnkSize).to_bytes(4,byteorder='little')
                    sbnkHeader[5] = (sbnkSize - 0x10).to_bytes(4,byteorder='little')
                    testPath = sysargv[outfileArg] + "/Files/" + itemString[2] + "/" + fName
                    with open(testPath, "wb") as sbnkFile:
                        for ii, listItem in enumerate(sbnkHeader):
                            sbnkFile.write(listItem)
                        for ii, listItem in enumerate(sbnkData):
                            sbnkFile.write(listItem)
                else:
                    print("\nMissing File:" + testPath)
                    quit()
        curFileLoc = (len(SDAT) + sum(len(tf) for tf in tFileBuffer))
        write_long((curFile * 16) + 12 + fatBlockOffset,curFileLoc) #write file pointer to the fatBlock
        with open(testPath, "rb") as tempFile:
                tFileBuffer.append(tempFile.read())
        write_long((curFile * 16) + 16 + fatBlockOffset,len(tFileBuffer[curFile]))#write file size to the fatBlock

        while (len(tFileBuffer[curFile]) & 0xFFFFFFE0) != len(tFileBuffer[curFile]):
            tFileBuffer[curFile] += b'\x00' #pad to the nearest 0x20 byte alignment
        curFile += 1
    write_long(16 + (headeri * 8), fileBlockOffset)
    write_long(20 + (headeri * 8), (len(SDAT) + sum(len(tf) for tf in tFileBuffer)) - fileBlockOffset)
    write_long(fileBlockOffset + 4, (len(SDAT) + sum(len(tf) for tf in tFileBuffer)) - fileBlockOffset) #write fileBlock size
    write_long(8, (len(SDAT) + sum(len(tf) for tf in tFileBuffer))) #write file size
    with open(sysargv[infileArg],"wb") as outfile:
        for i, character in enumerate(SDAT):
            outfile.write(character.to_bytes(1,byteorder='little'))
        for i, tFile in enumerate(tFileBuffer):
            outfile.write(tFile)
    ts2 = time.time() - ts
    print("Done: " + str(ts2) + "s")
