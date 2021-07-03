from const import itemExt

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


def read_long(sdat, pos=None):
    if pos:
        return int.from_bytes(sdat.data[pos:pos + 4], 'little')
    sdat.pos += 4
    return int.from_bytes(sdat.data[sdat.pos - 4:sdat.pos], 'little')


def read_short(sdat, pos=None):
    if pos:
        return int.from_bytes(sdat.data[pos:pos + 2], 'little')
    sdat.pos += 2
    return int.from_bytes(sdat.data[sdat.pos - 2:sdat.pos], 'little')


def read_byte(sdat, pos=None):
    if pos:
        return int.from_bytes(sdat.data[pos:pos + 1], 'little')
    sdat.pos += 1
    return int.from_bytes(sdat.data[sdat.pos - 1:sdat.pos], 'little')


def read_item_name(sdat, listItem):
    pointer = read_short(sdat)
    if pointer < len(sdat.names[listItem]):
        retString = sdat.names[listItem][pointer]
    else:
        if pointer == 65535 and listItem == WAVARC:  # unused wavarc slot
            retString = ""
        else:
            retString = f"{sdat.itemString[listItem]}_{pointer}"
    if listItem == PLAYER:
        sdat.pos -= 1  # Pointers for PLAYER are 1 byte
    return retString


def read_filename(sdat):
    tempID = read_short(sdat)
    matchID = 0
    done = False
    while matchID < len(sdat.fileNameID) and not done:
        if sdat.fileNameID[matchID] == tempID:
            done = True
        else:
            matchID += 1
    return sdat.names[FILE][matchID] + itemExt[sdat.fileType[matchID]]


def append_long(sdat, x):  # append a 32bit value to SDAT LSB first
    sdat.data += x.to_bytes(4, 'little')


def append_short(sdat, x):  # append a 16bit value to SDAT LSB first
    sdat.data += x.to_bytes(2, 'little')


def append_byte(sdat, x):  # append an 8bit value to SDAT
    sdat.data += x.to_bytes(1, 'little')


def write_long(sdat, loc, x):  # write a 32bit value to SDAT at position loc LSB first
    sdat.data[loc:loc + 4] = x.to_bytes(4, 'little')


def write_short(sdat, loc, x):  # write a 16bit value to SDAT at position loc LSB first
    sdat.data[loc:loc + 2] = x.to_bytes(2, 'little')


def write_byte(sdat, loc, x):  # write an 8bit value to SDAT at position loc
    sdat.data[loc] = x.to_bytes(1, 'little')


def get_string(sdat):
    retString = ""
    if sdat.pos <= 0x40:
        return ""
    i = sdat.data[sdat.pos]
    sdat.pos += 1
    while i > 0:
        retString += chr(i)
        i = sdat.data[sdat.pos]
        sdat.pos += 1
    return retString


