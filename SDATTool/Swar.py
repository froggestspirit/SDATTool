import os
from const import itemString
from util import read_long

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


def unpack_swar(sdat, tempPath):
    tempSize = read_long(sdat, pos=sdat.pos + 8)
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


def build_swar(sdat, args, fName, swavName):
    swarTemp = []
    for sName in swavName:
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
        for sFile in swarTemp:
            swarFile.write((swarPointer).to_bytes(4, byteorder='little'))
            swarPointer += len(sFile[0x18:])
        for sFile in swarTemp:
            swarFile.write(sFile[0x18:])
