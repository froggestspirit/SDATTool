#SDAT-Tool by FroggestSpirit
version = "0.8.1"
#Unpacks and builds SDAT files
#Make backups, this can overwrite files without confirmation

import sys
import os
import math
import hashlib
import time

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

itemString = []
itemParamString = []
itemExt = []
itemHeader = []
itemParams = []
itemOffset = []
itemSymbOffset = []
itemCount = []
itemData = {}
names = {}
namesUsed = {}
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
	if(name not in names[FILE]):
		if(optimize):
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
				if(thisMD5.hexdigest() not in fileMD5):
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
	if(not removeFlag): #skip this if the build is removing unused entries
		return True
	if(string == "NULL"): #skip item if null
		return False
	if(item in (SEQ, SEQARC, GROUP, PLAYER2, STRM)): #None of these get referenced from other items(?), so they should all be included
		return True
	if(string in namesUsed[item]):
		return True
	return False

def get_params(tList):
	global SDATPos
	retString = ""
	for i, listItem in enumerate(tList):
		tempString = ""
		if(i > 0):
			retString += ","
		if(listItem == BYTE):
			tempString = str(SDAT[SDATPos])
			retString += tempString
			SDATPos += 1
		elif (listItem == SHORT):
			tempString = str(read_short(SDATPos))
			retString += tempString
			SDATPos += 2
		elif (listItem == LONG):
			tempString = str(read_long(SDATPos))
			retString += tempString
			SDATPos += 4
		elif (listItem == FILE): #point to the file name
			tempID = read_short(SDATPos)
			matchID = 0
			done = False
			while(matchID < len(fileNameID) and not done):
				if(fileNameID[matchID] == tempID):
					done = True
				else:
					matchID += 1
			retString += names[FILE][matchID] + itemExt[fileType[matchID]]
			SDATPos += 2
		else: #point to the name of the item
			if(read_short(SDATPos) < len(names[listItem])):
				retString += names[listItem][read_short(SDATPos)]
			else:
				if(read_short(SDATPos) == 65535 and listItem == WAVARC): #unused wavarc slot
					retString += "NULL"
				else:
					retString += itemString[listItem] + "_" + str(read_short(SDATPos))
			SDATPos += 2
			if(listItem == PLAYER):
				SDATPos -= 1
	return retString

def convert_params(tArray,tList):
	retList = []
	retList.append(tArray[0])
	for i, listItem in enumerate(tList):
		if(listItem <= BYTE): #convert to integer
			retList.append(int(tArray[i + 1]))
		elif(listItem == FILE and optimize): #check file MD5 for duplicates
			matchID = 0
			done = False
			while(matchID < len(fileAll) and not done):
				if(fileAll[matchID] == tArray[i + 1]):
					done = True
				else:
					matchID += 1
			tempMD5 = fileAllMD5[matchID]
			matchID2 = 0
			done = False
			while(matchID2 < len(fileMD5) and not done):
				if(fileMD5[matchID2] == tempMD5):
					done = True
				else:
					matchID2 += 1
			retList.append(matchID2)
		else: #reference item by string
			matchID = 0
			done = False
			if(tArray[i + 1] == "NULL" and listItem == WAVARC): #unused bank
				done = True
				matchID = 65535
			while(matchID < len(names[listItem]) and not done):
				if(names[listItem][matchID] == tArray[i + 1]):
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
		if(listItem == BYTE or listItem == PLAYER): #parameter is an 8-bit write
			append_byte(itemData[item][index + i + 1])
		elif(listItem == LONG): #parameter is a 32-bit write
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
	if(SDATPos <= 0x40):
		return "NULL"
	i = SDAT[SDATPos]
	SDATPos += 1
	while(i > 0):
		retString += chr(i)
		i = SDAT[SDATPos]
		SDATPos += 1
	return retString
	
ts = time.time()
sysargv = sys.argv
echo = True
mode = 0
calcMD5 = False
optimize = False
skipSymbBlock = False
skipFileOrder = False
removeUnused = False

for i in range(9):
	names[i] = []
	namesUsed[i] = []
	itemData[i] = []
	itemParams.append([""])
	itemString.append("")
	itemParamString.append("")
	itemExt.append("")
	itemHeader.append("")
	itemCount.append(0)
	itemOffset.append(0)
	itemSymbOffset.append(0)

itemString[SEQ] = "SEQ"
itemString[SEQARC] = "SEQARC"
itemString[BANK] = "BANK"
itemString[WAVARC] = "WAVARC"
itemString[PLAYER] = "PLAYER"
itemString[GROUP] = "GROUP"
itemString[PLAYER2] = "PLAYER2"
itemString[STRM] = "STRM"
itemString[FILE] = "FILE"

itemParams[SEQ] = [FILE,SHORT,BANK,BYTE,BYTE,BYTE,PLAYER,BYTE,BYTE]
itemParams[SEQARC] = [FILE,SHORT]
itemParams[BANK] = [FILE,SHORT,WAVARC,WAVARC,WAVARC,WAVARC]
itemParams[WAVARC] = [FILE,SHORT]
itemParams[PLAYER] = [BYTE,BYTE,BYTE,BYTE,LONG]
itemParams[GROUP] = [LONG]
itemParams[PLAYER2] = [BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE]
itemParams[STRM] = [FILE,SHORT,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE,BYTE]

itemParamString[SEQ] = "SEQ(name,fileName,?,bnk,vol,cpr,ppr,ply,?[2]){\n"
itemParamString[SEQARC] = "SEQARC(name,fileName,?){\n"
itemParamString[BANK] = "BANK(name,fileName,?,wa[4]){\n"
itemParamString[WAVARC] = "WAVARC(name,fileName,?){\n"
itemParamString[PLAYER] = "PLAYER(name,?,padding[3],?){\n"
itemParamString[GROUP] = "GROUP(name,count[type,entries]){\n"
itemParamString[PLAYER2] = "PLAYER2(name,count,v[16],reserved[7]){\n"
itemParamString[STRM] = "STRM(name,fileName,?,vol,pri,ply,reserved[5]){\n"

itemExt[SEQ] = ".sseq"
itemExt[SEQARC] = ".ssar"
itemExt[BANK] = ".sbnk"
itemExt[WAVARC] = ".swar"
itemExt[STRM] = ".strm"

itemHeader[SEQ] = "SSEQ"
itemHeader[SEQARC] = "SSAR"
itemHeader[BANK] = "SBNK"
itemHeader[WAVARC] = "SWAR"
itemHeader[STRM] = "STRM"

print("SDAT-Tool " + version)
infileArg = -1;
outfileArg = -1;
for i, argument in enumerate(sysargv):
	if(i > 0):
		if(argument.startswith("-")):
			if(argument == "-u" or argument == "--unpack"):
				mode = 1
			elif(argument == "-b" or argument == "--build"):
				mode = 2
			elif(argument == "-h" or argument == "--help"):
				mode = 0
			elif(argument == "-m" or argument == "--md5"):
				calcMD5 = True
			elif(argument == "-o" or argument == "--optimize"):
				optimize = True
				skipFileOrder = True
			elif(argument == "-ru" or argument == "--removeUnused"):
				optimize = True
				skipFileOrder = True
				removeUnused = True
			elif(argument == "-ns" or argument == "--noSymbBlock"):
				skipSymbBlock = True
		else:
			if(infileArg == -1): infileArg=i
			elif(outfileArg == -1): outfileArg=i
			
if(infileArg == -1):
	mode = 0
else:
	if(outfileArg == -1):
		if(sysargv[infileArg].find(".sdat") != -1):
			if(mode == 0): mode = 1
			outfileArg=len(sysargv)
			sysargv.append(sysargv[infileArg].replace(".sdat",""))
		else:
			mode = 0
	else:
		if(sysargv[infileArg]==sysargv[outfileArg]):
			print("Input and output files cannot be the same")
			sys.exit()
if(mode == 0): #Help
	print("Usage: "+sysargv[0]+" [SDAT File] [mode] [SDAT Folder] [flags]\nMode:\n\t-b\tBuild SDAT\n\t-u\tUnpack SDAT\n\t-h\tShow this help message\n\nFlags:\n\t-m\tCalculate file MD5 when unpacking\n\t-o\tBuild Optimized\n\t-ru\tBuild without unused entries (can break games)\n\t-ns\tBuild without a SymbBlock\n")
	sys.exit()

if(mode == 1): #Unpack
	print("Unpacking...")
	if not os.path.exists(sysargv[outfileArg]):
		os.makedirs(sysargv[outfileArg])
	infile = open(sysargv[infileArg], "rb")
	SDAT = infile.read()
	infile.close()

	fileSize = len(SDAT)
	SDATSize = read_long(8)
	headerSize = read_short(12)
	blocks = read_short(14)
	global SDATPos
	SDATPos = 16
	if(blocks == 4):
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

	global outfile

	#Symb Block
	if(blocks == 4):
		SDATPos = symbOffset + 8
		for i in range(8):
			itemSymbOffset[i] = read_long(SDATPos + (i * 4)) + symbOffset

		for i in range(8):
			if(i != SEQARC):
				SDATPos = itemSymbOffset[i]
				entries = read_long(SDATPos)
				for ii in range(entries):
					SDATPos = read_long(itemSymbOffset[i] + 4 + (ii * 4)) + symbOffset
					names[i].append(get_string())
			else:
				SDATPos = itemSymbOffset[i]
				entries = read_long(SDATPos)
				if(entries > 0):
					outfile = open(sysargv[outfileArg] + "/SymbBlock.txt","w")
					outfile.write(itemString[i] + "{\n")
				for ii in range(entries):
					SDATPos = read_long(itemSymbOffset[i] + 4 + (ii * 8)) + symbOffset
					names[i].append(get_string())
					if(entries > 0):
						outfile.write(names[i][len(names[i]) - 1] + "\n")
					SDATPos = read_long(itemSymbOffset[i] + 8 + (ii * 8)) + symbOffset
					SEQARCSubOffset = SDATPos
					count = read_long(SDATPos)
					for x in range(count):
						SDATPos = read_long(SEQARCSubOffset + 4 + (x * 4)) + symbOffset
						if(entries > 0):
							outfile.write("\t" + get_string() + "\n")
				if(entries > 0):
					outfile.write("}\n")
					outfile.close()			

	#Info Block
	SDATPos = infoOffset + 8
	for i in range(8):
		itemOffset[i] = read_long(SDATPos + (i * 4)) + infoOffset
	outfile = open(sysargv[outfileArg] + "/InfoBlock.txt","w")
	
	for i in range(8):
		SDATPos = itemOffset[i]
		outfile.write(itemParamString[i])
		entries = read_long(SDATPos)
		for ii in range(entries):
			SDATPos = read_long(itemOffset[i] + 4 + (ii * 4)) + infoOffset
			if(SDATPos - infoOffset > 0x40):
				count = read_long(SDATPos) #count is only used for group
				if(blocks == 4 and ii < len(names[i])):
					iName = names[i][ii]
				else:
					iName = itemString[i] + "_" + str(ii)
				if(i in (SEQ, SEQARC, BANK, WAVARC, STRM)): #These have files
					fileType.append(i)
					fileNameID.append(read_short(SDATPos))
					names[FILE].append(iName)
				outfile.write(iName + "," + get_params(itemParams[i]))
				if(i == GROUP):
					for x in range(count):
						outfile.write("," + get_params([LONG,LONG]))
				outfile.write("\n")
			else:
				outfile.write("NULL\n")
		outfile.write("}\n\n")

	outfile.close()

	#FAT Block / File Block
	SDATPos = fatOffset + 8
	entries = read_long(SDATPos)
	IDFile = open(sysargv[outfileArg] + "/FileID.txt","w")
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
		if(fileHeader in itemHeader):
			tempPath = sysargv[outfileArg] + "/Files/" + itemString[itemHeader.index(fileHeader)] + "/" + "unknown_" + str(i)
			tempName = "unknown_" + str(i)
			tempExt = itemExt[itemHeader.index(fileHeader)]
		else:
			tempPath = sysargv[outfileArg] + "/Files/unknown_" + str(i)
			tempName = "unknown_" + str(i)
			tempExt = ""
		while(fileNameID[fileRefID] != i and not done):
			fileRefID += 1
			if(fileRefID >= len(fileNameID)):
				fileRefID = -1
				done = True
		if(fileRefID != -1):
			tempPath = sysargv[outfileArg] + "/Files/" + itemString[fileType[fileRefID]] + "/" + names[FILE][fileRefID]
			tempName = names[FILE][fileRefID]
		if(fileHeader == "SWAR"):
			numSwav = read_long(SDATPos + 0x38)
			if not os.path.exists(tempPath):
				os.makedirs(tempPath)
			swavIDFile = open(tempPath + "/FileID.txt","w")
			for i in range(numSwav):
				swavOffset = SDATPos + read_long(SDATPos + (i * 4) + 0x3C)
				swavLength = SDATPos + read_long(SDATPos + ((i + 1) * 4) + 0x3C)
				if(i + 1 == numSwav):
					swavLength = SDATPos+tempSize
				swavSize = swavLength - swavOffset
				outfile = open(tempPath + "/" + str(i) + ".swav","wb")
				outfile.write(b'SWAV') #Header
				outfile.write(b'\xFF\xFE\x00\x01') #magic
				outfile.write((swavSize + 0x18).to_bytes(4,byteorder='little'))
				outfile.write(b'\x10\x00\x01\x00') #structure size and blocks
				outfile.write(b'DATA')
				outfile.write((swavSize + 0x08).to_bytes(4,byteorder='little'))
				outfile.write(SDAT[swavOffset:swavLength])
				outfile.close()
				swavIDFile.write(str(i) + ".swav\n")
			swavIDFile.close()
		else:
			outfile = open(tempPath + tempExt,"wb")
			outfile.write(SDAT[SDATPos:SDATPos+tempSize])
			outfile.close()
		tempFileString = SDAT[SDATPos:SDATPos+tempSize]
		IDFile.write(tempName + tempExt)
		if(calcMD5):
			thisMD5 = hashlib.md5(tempFileString)
			IDFile.write(";MD5 = " + thisMD5.hexdigest())
		IDFile.write("\n")
	IDFile.close()
	ts2 = time.time() - ts
	print("Done: " + str(ts2) + "s")

if(mode == 2): #Build
	print("Building...")
	blocks = 4
	if(skipSymbBlock):
		blocks = 3	
	if not os.path.exists(sysargv[outfileArg] + "/FileID.txt"):
		print("\nMissing FileID.txt, files will be ordered as they are in the InfoBlock.\n")
		skipFileOrder = True
	if not os.path.exists(sysargv[outfileArg] + "/InfoBlock.txt"):
		print("\nMissing InfoBlock.txt\n")
		quit()

	if(not skipFileOrder):
		IDFile = open(sysargv[outfileArg] + "/FileID.txt", "r")
		done = False
		while(not done):
			thisLine = IDFile.readline()
			if not thisLine:
				done = True
			thisLine = thisLine.split(";") #ignore anything commented out
			thisLine = thisLine[0]
			thisLine = thisLine.split("\n") #remove newline
			thisLine = thisLine[0]
			if(thisLine != ""):
				names[FILE].append(thisLine)
				itemCount[FILE] += 1
		IDFile.close() #file names are stored now

	infoFile = open(sysargv[outfileArg] + "/InfoBlock.txt", "r")

	seqarcSymbSubCount = [] #keep track of how many sub strings are in each seqarc
	for i in range(8):
		done = False
		while(not done):
			thisLine = infoFile.readline()
			if not thisLine:
				done = True
			thisLine = thisLine.split(";") #ignore anything commented out
			thisLine = thisLine[0]
			thisLine = thisLine.split("\n") #remove newline
			thisLine = thisLine[0]
			if(thisLine.find("{") == -1): #ignore lines with {
				if(thisLine.find("}") != -1): #end of section
					done = True
				elif(thisLine != ""):
					thisLine = thisLine.split(",") #split parameters
					if(check_unused(removeUnused, i, thisLine[0])):
						names[i].append(thisLine[0])
						if(i == SEQARC):
							seqarcSymbSubCount.append(0)
						if(thisLine[0] != "NULL"):
							if(skipFileOrder and itemParams[i][0] == FILE):
								add_fileName(thisLine[1])
							for ii, param in enumerate(itemParams[i]):
								if(param >= 0):
									namesUsed[param].append(thisLine[ii + 1])

	infoFile.close() #names of the entries of groups are now stored

	if(blocks == 4 and os.path.exists(sysargv[outfileArg] + "/SymbBlock.txt")):
		symbFile = open(sysargv[outfileArg] + "/SymbBlock.txt", "r")
		thisLine = ""
		seqarcSymbSubNum = 0
		done = False
		seqarcSymbSubParent = []
		seqarcSymbSubName = []
		mainSEQARCID = -1
		while(not done):
			thisLine = symbFile.readline()
			if not thisLine:
				done = True
			thisLine = thisLine.split(";") #ignore anything commented out
			thisLine = thisLine[0]
			thisLine = thisLine.split("\n") #remove newline
			thisLine = thisLine[0]
			if(thisLine.find("{") == -1): #ignore lines with {
				if(thisLine.find("}") != -1): #end of section
					done = True
				elif(thisLine != ""):
					if(thisLine[:1] == "\t"): #is a sub string
						if(mainSEQARCID != -1):
							seqarcSymbSubName.append(thisLine[1:])
							seqarcSymbSubParent.append(mainSEQARCID)
							seqarcSymbSubNum += 1
					else: #not a sub string
						tempID = 0
						done2 = False
						while(tempID < len(names[SEQARC]) and not done2):
							if(names[SEQARC][tempID] == thisLine):
								done2 = True
							else:
								tempID += 1
						if(done2):
							if(mainSEQARCID != -1):
								seqarcSymbSubCount[mainSEQARCID] = seqarcSymbSubNum
							mainSEQARCID = tempID
							seqarcSymbSubNum = 0
						else:
							mainSEQARCID = -1

		if(mainSEQARCID != -1):
			seqarcSymbSubCount[mainSEQARCID] = seqarcSymbSubNum
		symbFile.close() #symb strings are stored now

	infoFile = open(sysargv[outfileArg] + "/InfoBlock.txt", "r")
	for i in range(8):
		done = False
		params = len(itemParams[i]) + 1
		while(not done):
			thisLine = infoFile.readline()
			if not thisLine:
				done = True
			thisLine = thisLine.split(";") #ignore anything commented out
			thisLine = thisLine[0]
			thisLine = thisLine.split("\n") #remove newline
			thisLine = thisLine[0]
			if(thisLine.find("{") == -1): #ignore lines with {
				if(thisLine.find("}") != -1): #end of section
					done = True
				elif(thisLine != ""):
					thisLine = thisLine.split(",") #split parameters
					if(check_unused(removeUnused, i, thisLine[0])):
						if(thisLine[0] == "NULL"):
							itemData[i].append("NULL")
							for ii in range(params - 1):
								itemData[i].append(0)
							itemCount[i] += 1
						else:
							if(i == GROUP):
								params = (int(thisLine[1]) * 2) + 2
								for ii, number in enumerate(thisLine[1:]):
									thisLine[ii + 1] = int(number) #convert ID to an integer
							if(len(thisLine) != params):
								print("\n" + itemString[i] + " wrong number of parameters.\n")
								quit()
							if(i != GROUP):
								thisLine = convert_params(thisLine,itemParams[i])
							for ii in range(params):
								itemData[i].append(thisLine[ii])
							itemCount[i] += 1
	infoFile.close()

	append_list([ord('S'),ord('D'),ord('A'),ord('T')]) #Header
	append_list([0xFF,0xFE,0x00,0x01]) #Magic
	append_reserve(4) #File size
	append_short((blocks + 4) * 8) #Header size
	append_short(blocks) #Blocks
	append_reserve((blocks + 2) * 8) #reserve space for the offsets and sizes
	headeri = 0 #help point back to the block offsets and sizes when ready to write

	if(blocks == 4): #symbBlock
		symbBlockOffset = len(SDAT)
		append_list([ord('S'),ord('Y'),ord('M'),ord('B')]) #Header
		append_reserve(4) #symbBlock size
		append_reserve(8 * 4) #reserve space for the offsets
		append_reserve(24) #reserved bytes

		for i in range(8):
			if(i != SEQARC):
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
			if(i != SEQARC):
				for ii in range(itemCount[i]):
					if(names[i][ii] != "NULL"):
						write_long((itemSymbOffset[i] + 4) + (ii * 4), len(SDAT) - symbBlockOffset)
						for x, character in enumerate(names[i][ii]):
							append_byte(ord(character))
						append_byte(0) #terminate string
			else:
				for ii in range(itemCount[i]):
					if(names[i][ii] != "NULL"):
						write_long((itemSymbOffset[i] + 4) + (ii * 8), len(SDAT) - symbBlockOffset)
						for x, character in enumerate(names[i][ii]):
							append_byte(ord(character))
						append_byte(0) #terminate string
						curSeqarcSub = 0
						for subi, name in enumerate(seqarcSymbSubName):
							if(seqarcSymbSubParent[subi] == ii):
								if(name != "NULL"):
									write_long((seqarcSymbSubOffset[ii] + 4) + (curSeqarcSub * 4), len(SDAT) - symbBlockOffset)
									for x, character in enumerate(name):
										append_byte(ord(character))
									append_byte(0) #terminate string
								curSeqarcSub += 1

		write_long(16, symbBlockOffset)
		write_long(20, len(SDAT) - symbBlockOffset)
		headeri += 1
		while((len(SDAT) & 0xFFFFFFFC) != len(SDAT)):
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
		if(i != GROUP):
			params = len(itemParams[i]) + 1
			for ii in range(itemCount[i]):
				if(itemData[i][(ii * params)] != "NULL"):
					write_long((itemOffset[i] + 4) + (ii * 4), len(SDAT) - infoBlockOffset)
					append_params(i,(ii * params),itemParams[i])
		else:
			ii = 0
			entry = 0
			while(ii < len(itemData[i])):
				if(itemData[i][ii] != "NULL"):
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
	while((len(SDAT) & 0xFFFFFFFC) != len(SDAT)):
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
	while((len(SDAT) & 0xFFFFFFFC) != len(SDAT)):
		append_reserve(1) #pad to the nearest 0x04 byte alignment
	write_long(fatBlockOffset + 4, len(SDAT) - fatBlockOffset)

	fileBlockOffset = len(SDAT) #fileBlock
	append_list([ord('F'),ord('I'),ord('L'),ord('E')]) #Header
	append_reserve(4) #fileBlock size
	append_long(itemCount[FILE]) #number of files
	append_reserve(4) #reserved
	while((len(SDAT) & 0xFFFFFFE0) != len(SDAT)):
		append_reserve(1) #pad to the nearest 0x20 byte alignment

	curFile = 0
	tFileBuffer = []
	for i, fName in enumerate(names[FILE]):
		testPath = sysargv[outfileArg] + "/Files/" + itemString[itemExt.index(fName[-5:])] + "/" + fName
		if not os.path.exists(testPath):
			testPath = sysargv[outfileArg] + "/Files/" + fName
			if not os.path.exists(testPath):
				if(fName[-5:] == ".swar"):#can the swar be built?
					testPath = sysargv[outfileArg] + "/Files/" + itemString[3] + "/" + fName[:-5] + "/FileID.txt"
					if not os.path.exists(testPath):
						print("\nMissing File:" + testPath)
						quit()
					swavIDFile = open(testPath, "r")
					done = False
					swavName = []
					while(not done):
						thisLine = swavIDFile.readline()
						if not thisLine:
							done = True
						thisLine = thisLine.split(";") #ignore anything commented out
						thisLine = thisLine[0]
						thisLine = thisLine.split("\n") #remove newline
						thisLine = thisLine[0]
						if(thisLine != ""):
							swavName.append(thisLine)
					swavIDFile.close() #file names are stored now
					swarTemp = []
					for ii, sName in enumerate(swavName):
						testPath = sysargv[outfileArg] + "/Files/" + itemString[3] + "/" + fName[:-5] + "/" + sName
						if not os.path.exists(testPath):
							print("\nMissing File:" + testPath)
							quit()
						tempFile = open(testPath, "rb")
						swarTemp.append(tempFile.read())
						tempFile.close()
					testPath = sysargv[outfileArg] + "/Files/" + itemString[3] + "/" + fName
					swarFile = open(testPath, "wb")
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
					swarFile.close()
				else:
					print("\nMissing File:" + testPath)
					quit()
		curFileLoc = (len(SDAT) + sum(len(tf) for tf in tFileBuffer))
		write_long((curFile * 16) + 12 + fatBlockOffset,curFileLoc) #write file pointer to the fatBlock
		tempFile = open(testPath, "rb")
		tFileBuffer.append(tempFile.read())
		tempFile.close()
		write_long((curFile * 16) + 16 + fatBlockOffset,len(tFileBuffer[curFile]))#write file size to the fatBlock

		while((len(tFileBuffer[curFile]) & 0xFFFFFFE0) != len(tFileBuffer[curFile])):
			tFileBuffer[curFile] += b'\x00' #pad to the nearest 0x20 byte alignment
		curFile += 1
	write_long(16 + (headeri * 8), fileBlockOffset)
	write_long(20 + (headeri * 8), (len(SDAT) + sum(len(tf) for tf in tFileBuffer)) - fileBlockOffset)
	write_long(fileBlockOffset + 4, (len(SDAT) + sum(len(tf) for tf in tFileBuffer)) - fileBlockOffset) #write fileBlock size
	
	write_long(8, (len(SDAT) + sum(len(tf) for tf in tFileBuffer))) #write file size

	outfile = open(sysargv[infileArg],"wb")
	for i, character in enumerate(SDAT):
		outfile.write(character.to_bytes(1,byteorder='little'))
	for i, tFile in enumerate(tFileBuffer):
		outfile.write(tFile)
	outfile.close()
	ts2 = time.time() - ts
	print("Done: " + str(ts2) + "s")
