#!/usr/bin/python3
# SDAT-Tool by FroggestSpirit
version = "1.4.0"
# Unpacks and builds SDAT files
# Make backups, this can overwrite files without confirmation

import os
import time
import argparse
import json
from shutil import copyfile

from const import itemExt, itemString, infoBlockGroup, infoBlockGroupFile
from Sseq import seqNote
from Sdat import SDAT, InfoBlock, FileBlock, unpack_symbBlock, unpack_infoBlock, unpack_fileBlock, \
                 build_symbBlock, build_infoBlock, build_fatBlock, build_fileBlock
from util import write_long

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
    sdat = SDAT(fileName=args.SDATfile)

    # Symb Block
    unpack_symbBlock(sdat)                          

    # Info Block
    unpack_infoBlock(sdat)
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
    unpack_fileBlock(sdat, args)
    with open(f"{args.folder}/FileBlock.json", "w") as outfile:
        outfile.write(json.dumps(sdat.fileBlock, cls=MyEncoder, indent=4))


def build(args):  # Build
    if not os.path.exists(f"{args.folder}/FileBlock.json"):
        raise Exception("Missing FileBlock.json\n")
    if not os.path.exists(f"{args.folder}/InfoBlock.json"):
        raise Exception("Missing InfoBlock.json\n")
    print("Building...")
    sdat = SDAT(noSymbBlock=args.noSymbBlock)

    with open(f"{args.folder}/InfoBlock.json", "r") as infile:
        sdat.infoBlock = InfoBlock()
        sdat.infoBlock.load(sdat, json.load(infile))
    with open(f"{args.folder}/FileBlock.json", "r") as infile:
        sdat.fileBlock = FileBlock()
        sdat.fileBlock.load(json.load(infile))

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
                                        elif sseqLines[curLine].replace("\t","")[:2] in seqNote:
                                            curNote = seqNote.index(sseqLines[curLine].replace("\t","")[:2]) + (int(sseqLines[curLine][3]) * 12)
                                            if not (curInst << 7) + curNote in tempInstUsed:
                                                tempInstUsed.append((curInst << 7) + curNote)
                                                testvar = seqNote.index(sseqLines[curLine].replace("\t","")[:2])
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
    sdat.seqarcSymbSubParent = []
    sdat.seqarcSymbSubName = []
    sdat.seqarcSymbSubCount = []
    for i in sdat.infoBlock.seqarcInfo:
        sdat.names[SEQARC].append(i.name)
        for ii in i.zippedName:
            sdat.seqarcSymbSubParent.append(len(sdat.names[SEQARC]) - 1)
            sdat.seqarcSymbSubName.append(ii)
        sdat.seqarcSymbSubCount.append(len(i.zippedName))
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

    build_symbBlock(sdat)

    build_infoBlock(sdat)

    build_fatBlock(sdat)

    build_fileBlock(sdat, args)

    curFile = 0
    tFileBuffer = []
    for i, fName in enumerate(sdat.names[FILE]):  # Pack the binary files
        testPath = f"{args.folder}/Files/{itemString[itemExt.index(fName[-5:])]}/{fName}"
        if not os.path.exists(testPath):
            testPath = f"{args.folder}/Files/{fName}"
            if not os.path.exists(testPath):
                raise Exception(f"Missing File:{testPath}")
        curFileLoc = (len(sdat.data) + sum(len(tf) for tf in tFileBuffer))
        write_long(sdat, (curFile * 16) + 12 + sdat.fatBlockOffset, curFileLoc)  # write file pointer to the fatBlock
        with open(testPath, "rb") as tempFile:
            tFileBuffer.append(bytearray(tempFile.read()))
        write_long(sdat, (curFile * 16) + 16 + sdat.fatBlockOffset, len(tFileBuffer[curFile]))  # write file size to the fatBlock

        while (len(tFileBuffer[curFile]) & 0xFFFFFFE0) != len(tFileBuffer[curFile]):
            tFileBuffer[curFile] += b'\x00'  # pad to the nearest 0x20 byte alignment
        curFile += 1
    write_long(sdat, 16 + (sdat.headeri * 8), sdat.fileBlockOffset)
    write_long(sdat, 20 + (sdat.headeri * 8), (len(sdat.data) + sum(len(tf) for tf in tFileBuffer)) - sdat.fileBlockOffset)
    write_long(sdat, sdat.fileBlockOffset + 4, (len(sdat.data) + sum(len(tf) for tf in tFileBuffer)) - sdat.fileBlockOffset)  # write fileBlock size
    write_long(sdat, 8, (len(sdat.data) + sum(len(tf) for tf in tFileBuffer)))  # write file size
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
    parser.add_argument("-wr", "--writeRaw", dest="writeRaw", action="store_true", help="Extract raw files")
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
