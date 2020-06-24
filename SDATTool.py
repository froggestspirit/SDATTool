#SDAT-Tool by FroggestSpirit
version = "0.0.3"
#Unpacks and builds SDAT files
#Make backups, this can overwrite files without confirmation

import sys
import os
import math
import hashlib

def read_long(pos):
	global SDAT
	return (SDAT[pos + 3] * 0x1000000) + (SDAT[pos + 2] * 0x10000) + (SDAT[pos + 1] * 0x100) + SDAT[pos]
	
def read_short(pos):
	global SDAT
	return (SDAT[pos + 1] * 0x100) + SDAT[pos]
	
def get_params(list):
	global SDATPos
	global SEQNames
	global SEQARCNames
	global BANKNames
	global WAVEARCNames
	global PLAYERNames
	global GROUPNames
	global PLAYER2Names
	global STRMNames
	global fileType
	global fileNameID
	global fileName

	retString = ""
	for i in range(len(list)):
		tempString = ""
		if(i > 0):
			retString += ","
		if(list[i] == 1):
			tempString = str(SDAT[SDATPos])
			retString += tempString
			SDATPos += 1
		elif (list[i] == 2):
			tempString = str(read_short(SDATPos))
			retString += tempString
			SDATPos += 2
		elif (list[i] == 4):
			tempString = str(read_long(SDATPos))
			retString += tempString
			SDATPos += 4
		elif (list[i] == 10): #point to the filename
			tempID = read_short(SDATPos)
			matchID = 0
			done = False
			while(matchID < len(fileNameID) and not done):
				if(fileNameID[matchID] == tempID):
					done = True
				else:
					matchID += 1
			retString += fileName[matchID] + fileType[matchID]
			SDATPos += 2
		elif (list[i] == 22): #point to the name of the bank
			if(read_short(SDATPos) < len(BANKNames)):
				retString += BANKNames[read_short(SDATPos)]
			else:
				retString += "BANK_" + str(read_short(SDATPos))
			SDATPos += 2
		elif (list[i] == 23): #point to the name of the wavarc
			if(read_short(SDATPos) < len(WAVEARCNames)):
				retString += WAVEARCNames[read_short(SDATPos)]
			else:
				if(read_short(SDATPos) == 65535): #unused slot
					retString += "NULL"
				else:
					retString += "WAVARC_" + str(read_short(SDATPos))
			SDATPos += 2
	return retString

def convert_params(tArray,list):
	global SEQNames
	global SEQARCNames
	global BANKNames
	global WAVEARCNames
	global PLAYERNames
	global GROUPNames
	global PLAYER2Names
	global STRMNames
	global fileName

	retList = []
	retList.append(tArray[0])
	for i in range(len(list)):
		tempString = ""
		if(list[i] == 0): #convert to integer
			retList.append(int(tArray[i + 1]))
		elif (list[i] == 10): #reference file by string
			matchID = 0
			done = False
			while(matchID < len(fileName) and not done):
				if(fileName[matchID] == tArray[i + 1]):
					done = True
				else:
					matchID += 1
			retList.append(matchID)
		elif (list[i] == 22): #reference bank by string
			matchID = 0
			done = False
			while(matchID < len(BANKNames) and not done):
				if(BANKNames[matchID] == tArray[i + 1]):
					done = True
				else:
					matchID += 1
			retList.append(matchID)
		elif (list[i] == 23): #reference wavearc by string
			matchID = 0
			done = False
			if(tArray[i + 1] == "NULL"): #unused bank
				done = True
				matchID = 65535
			while(matchID < len(WAVEARCNames) and not done):
				if(WAVEARCNames[matchID] == tArray[i + 1]):
					done = True
				else:
					matchID += 1
			retList.append(matchID)
	return retList

def append_list(list): #append a list of bytes to SDAT
	global SDAT
	for i in range(len(list)):
		SDAT.append(list[i])

def append_reserve(x): #append a number of 0x00 bytes to SDAT
	global SDAT
	for i in range(x):
		SDAT.append(0)

def append_long(x): #append a 32bit value to SDAT LSB first
	global SDAT
	SDAT.append((x & 0xFF))
	x = x >> 8
	SDAT.append((x & 0xFF))
	x = x >> 8
	SDAT.append((x & 0xFF))
	x = x >> 8
	SDAT.append((x & 0xFF))

def append_short(x): #append a 16bit value to SDAT LSB first
	global SDAT
	SDAT.append((x & 0xFF))
	x = x >> 8
	SDAT.append((x & 0xFF))	

def append_byte(x): #append an 8bit value to SDAT
	global SDAT
	SDAT.append((x & 0xFF))

def write_long(loc, x): #write a 32bit value to SDAT at position loc LSB first
	global SDAT
	SDAT[loc] = (x & 0xFF)
	x = x >> 8
	SDAT[loc+1] = (x & 0xFF)
	x = x >> 8
	SDAT[loc+2] = (x & 0xFF)
	x = x >> 8
	SDAT[loc+3] = (x & 0xFF)	

def write_short(loc, x): #write a 16bit value to SDAT at position loc LSB first
	global SDAT
	SDAT[loc] = (x & 0xFF)
	x = x >> 8
	SDAT[loc+1] = (x & 0xFF)	

def write_byte(loc, x): #write an 8bit value to SDAT at position loc
	global SDAT
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
	
sysargv = sys.argv
echo = True
mode = 0
calcMD5 = False
global SDAT

global SEQNames
global SEQARCNames
global BANKNames
global WAVEARCNames
global PLAYERNames
global GROUPNames
global PLAYER2Names
global STRMNames
global fileType
global fileNameID
global fileName

print("SDAT-Tool " + version + "\n")
infileArg = -1;
outfileArg = -1;
for i in range(len(sysargv)):
	if(i > 0):
		if(sysargv[i].startswith("-")):
			if(sysargv[i] == "-u" or sysargv[i] == "--unpack"):
				mode=1
			elif(sysargv[i] == "-b" or sysargv[i] == "--build"):
				mode=2
			elif(sysargv[i] == "-h" or sysargv[i] == "--help"):
				mode=0
			elif(sysargv[i] == "-m" or sysargv[i] == "--md5"):
				calcMD5 = True
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
	print("Usage: "+sysargv[0]+" [SDAT File] [mode] [SDAT Folder] [flags]\nMode:\n\t-b\tBuild SDAT\n\t-u\tUnpack SDAT\n\t-h\tShow this help message\n\nFlags:\n\t-m\tCalculate file MD5 when unpacking\n")
	sys.exit()

if(mode == 1): #Unpack
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
		SEQOffset = read_long(SDATPos) + symbOffset
		SEQARCOffset = read_long(SDATPos + 4) + symbOffset
		BANKOffset = read_long(SDATPos + 8) + symbOffset
		WAVEARCOffset = read_long(SDATPos + 12) + symbOffset
		PLAYEROffset = read_long(SDATPos + 16) + symbOffset
		GROUPOffset = read_long(SDATPos + 20) + symbOffset
		PLAYER2Offset = read_long(SDATPos + 24) + symbOffset
		STRMOffset = read_long(SDATPos + 28) + symbOffset

		SEQNames = []
		outfile = open(sysargv[outfileArg] + "/SymbBlock.txt","w")
		SDATPos = SEQOffset
		entries = read_long(SDATPos)
		outfile.write("SEQ{\n")
		for i in range(entries):
			SDATPos = read_long(SEQOffset + 4 + (i * 4)) + symbOffset
			SEQNames.append(get_string())
			outfile.write(SEQNames[len(SEQNames) - 1] + "\n")
		outfile.write("}\n\n")

		SEQARCNames = []
		SDATPos = SEQARCOffset
		entries = read_long(SDATPos)
		outfile.write("SEQARC{\n")
		for i in range(entries):
			SDATPos = read_long(SEQARCOffset + 4 + (i * 8)) + symbOffset
			SEQARCNames.append(get_string())
			outfile.write(SEQARCNames[len(SEQARCNames) - 1] + "\n")
			SDATPos = read_long(SEQARCOffset + 8 + (i * 8)) + symbOffset
			SEQARCSubOffset = SDATPos
			count = read_long(SDATPos)
			for ii in range(count):
				SDATPos = read_long(SEQARCSubOffset + 4 + (ii * 4)) + symbOffset
				outfile.write("\t" + get_string() + "\n")
		outfile.write("}\n\n")

		BANKNames = []
		SDATPos = BANKOffset
		entries = read_long(SDATPos)
		outfile.write("BANK{\n")
		for i in range(entries):
			SDATPos = read_long(BANKOffset + 4 + (i * 4)) + symbOffset
			BANKNames.append(get_string())
			outfile.write(BANKNames[len(BANKNames) - 1] + "\n")
		outfile.write("}\n\n")

		WAVEARCNames = []
		SDATPos = WAVEARCOffset
		entries = read_long(SDATPos)
		outfile.write("WAVEARC{\n")
		for i in range(entries):
			SDATPos = read_long(WAVEARCOffset + 4 + (i * 4)) + symbOffset
			WAVEARCNames.append(get_string())
			outfile.write(WAVEARCNames[len(WAVEARCNames) - 1] + "\n")
		outfile.write("}\n\n")

		PLAYERNames = []
		SDATPos = PLAYEROffset
		entries = read_long(SDATPos)
		outfile.write("PLAYER{\n")
		for i in range(entries):
			SDATPos = read_long(PLAYEROffset + 4 + (i * 4)) + symbOffset
			PLAYERNames.append(get_string())
			outfile.write(PLAYERNames[len(PLAYERNames) - 1] + "\n")
		outfile.write("}\n\n")

		GROUPNames = []
		SDATPos = GROUPOffset
		entries = read_long(SDATPos)
		outfile.write("GROUP{\n")
		for i in range(entries):
			SDATPos = read_long(GROUPOffset + 4 + (i * 4)) + symbOffset
			GROUPNames.append(get_string())
			outfile.write(GROUPNames[len(GROUPNames) - 1] + "\n")
		outfile.write("}\n\n")

		PLAYER2Names = []
		SDATPos = PLAYER2Offset
		entries = read_long(SDATPos)
		outfile.write("PLAYER2{\n")
		for i in range(entries):
			SDATPos = read_long(PLAYER2Offset + 4 + (i * 4)) + symbOffset
			PLAYER2Names.append(get_string())
			outfile.write(PLAYER2Names[len(PLAYER2Names) - 1] + "\n")
		outfile.write("}\n\n")

		STRMNames = []
		SDATPos = STRMOffset
		entries = read_long(SDATPos)
		outfile.write("STRM{\n")
		for i in range(entries):
			SDATPos = read_long(STRMOffset + 4 + (i * 4)) + symbOffset
			STRMNames.append(get_string())
			outfile.write(STRMNames[len(STRMNames) - 1] + "\n")
		outfile.write("}\n\n")

		outfile.close()

	#Info Block
	SDATPos = infoOffset + 8
	SEQOffset = read_long(SDATPos) + infoOffset
	SEQARCOffset = read_long(SDATPos + 4) + infoOffset
	BANKOffset = read_long(SDATPos + 8) + infoOffset
	WAVEARCOffset = read_long(SDATPos + 12) + infoOffset
	PLAYEROffset = read_long(SDATPos + 16) + infoOffset
	GROUPOffset = read_long(SDATPos + 20) + infoOffset
	PLAYER2Offset = read_long(SDATPos + 24) + infoOffset
	STRMOffset = read_long(SDATPos + 28) + infoOffset
	outfile = open(sysargv[outfileArg] + "/InfoBlock.txt","w")

	fileType = []
	fileNameID = []
	fileName = []
	SDATPos = SEQOffset
	outfile.write("SEQ(fileID,?,bnk,vol,cpr,ppr,ply,?[2]){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(SEQOffset + 4 + (i * 4)) + infoOffset
		if(SDATPos - infoOffset > 0x40):
			fileType.append(".sseq")
			fileNameID.append(read_short(SDATPos))
			if(blocks == 4 and i < len(SEQNames)):
				fileName.append(SEQNames[i])
				outfile.write(SEQNames[i] + "," + get_params([10,2,22,1,1,1,1,1,1]) + "\n")
			else:
				fileName.append("SEQ_" + str(i))
				outfile.write("SEQ_" + str(i) + "," + get_params([10,2,22,1,1,1,1,1,1]) + "\n")
		else:
			outfile.write("NULL\n")
	outfile.write("}\n\n")

	SDATPos = SEQARCOffset
	outfile.write("SEQARC(fileID,?){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(SEQARCOffset + 4 + (i * 4)) + infoOffset
		if(SDATPos - infoOffset > 0x40):
			fileType.append(".ssar")
			fileNameID.append(read_short(SDATPos))
			if(blocks == 4 and i < len(SEQARCNames)):
				fileName.append(SEQARCNames[i])
				outfile.write(SEQARCNames[i] + "," + get_params([10,2]) + "\n")
			else:
				fileName.append("SEQARC_" + str(i))
				outfile.write("SEQARC_" + str(i) + "," + get_params([10,2]) + "\n")
		else:
			outfile.write("NULL\n")
	outfile.write("}\n\n")

	SDATPos = BANKOffset
	outfile.write("BANK(fileID,?,wa[4]){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(BANKOffset + 4 + (i * 4)) + infoOffset
		if(SDATPos - infoOffset > 0x40):
			fileType.append(".sbnk")
			fileNameID.append(read_short(SDATPos))
			if(blocks == 4 and i < len(BANKNames)):
				fileName.append(BANKNames[i])
				outfile.write(BANKNames[i] + "," + get_params([10,2,23,23,23,23]) + "\n")
			else:
				fileName.append("BANK_" + str(i))
				outfile.write("BANK_" + str(i) + "," + get_params([10,2,23,23,23,23]) + "\n")
		else:
			outfile.write("NULL\n")
	outfile.write("}\n\n")

	SDATPos = WAVEARCOffset
	outfile.write("WAVEARC(fileID,?){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(WAVEARCOffset + 4 + (i * 4)) + infoOffset
		if(SDATPos - infoOffset > 0x40):
			fileType.append(".swar")
			fileNameID.append(read_short(SDATPos))
			if(blocks == 4 and i < len(WAVEARCNames)):
				fileName.append(WAVEARCNames[i])
				outfile.write(WAVEARCNames[i] + "," + get_params([10,2]) + "\n")
			else:
				fileName.append("WAVARC_" + str(i))
				outfile.write("WAVARC_" + str(i) + "," + get_params([10,2]) + "\n")
		else:
			outfile.write("NULL\n")
	outfile.write("}\n\n")

	SDATPos = PLAYEROffset
	outfile.write("PLAYER(?,padding[3],?){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(PLAYEROffset + 4 + (i * 4)) + infoOffset
		if(SDATPos - infoOffset > 0x40):
			if(blocks == 4 and i < len(PLAYERNames)):
				outfile.write(PLAYERNames[i] + "," + get_params([1,1,1,1,4]) + "\n")
			else:
				outfile.write("PLAYER_" + str(i) + "," + get_params([1,1,1,1,4]) + "\n")
		else:
			outfile.write("NULL\n")
	outfile.write("}\n\n")

	SDATPos = GROUPOffset
	outfile.write("GROUP(count[type,entries]){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(GROUPOffset + 4 + (i * 4)) + infoOffset
		if(SDATPos - infoOffset > 0x40):
			count = read_long(SDATPos)
			if(blocks == 4 and i < len(GROUPNames)):
				outfile.write(GROUPNames[i] + "," + get_params([4]))
			else:
				outfile.write("GROUP_" + str(i) + "," + get_params([4]))
			for ii in range(count):
					outfile.write("," + get_params([4,4]))
			outfile.write("\n")
		else:
			outfile.write("NULL\n")
	outfile.write("}\n\n")

	SDATPos = PLAYER2Offset
	outfile.write("PLAYER2(count,v[16],reserved[7]){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(PLAYER2Offset + 4 + (i * 4)) + infoOffset
		if(SDATPos - infoOffset > 0x40):
			if(blocks == 4 and i < len(PLAYER2Names)):
				outfile.write(PLAYER2Names[i] + "," + get_params([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]) + "\n")
			else:
				outfile.write("PLAYER2_" + str(i) + "," + get_params([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]) + "\n")
		else:
			outfile.write("NULL\n")
	outfile.write("}\n\n")

	SDATPos = STRMOffset
	outfile.write("STRM(fileID,?,vol,pri,ply,reserved[5]){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(STRMOffset + 4 + (i * 4)) + infoOffset
		if(SDATPos - infoOffset > 0x40):
			fileType.append(".strm")
			fileNameID.append(read_short(SDATPos))
			if(blocks == 4 and i < len(STRMNames)):
				fileName.append(STRMNames[i])
				outfile.write(STRMNames[i] + "," + get_params([10,2,1,1,1,1,1,1,1,1]) + "\n")
			else:
				fileName.append("STRM_" + str(i))
				outfile.write("STRM_" + str(i) + "," + get_params([10,2,1,1,1,1,1,1,1,1]) + "\n")
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
	for i in range(entries):
		SDATPos = read_long(fatOffset + 12 + (i * 16))
		tempSize = read_long(fatOffset + 16 + (i * 16))
		tempFile = []
		tempFileString = ""
		done = False
		fileRefID = 0
		while(fileNameID[fileRefID] != i and not done):
			fileRefID += 1
			if(fileRefID >= len(fileNameID)):
				fileRefID = -1
				done = True
		if(fileRefID == -1):
			outfile = open(sysargv[outfileArg] + "/Files/unknown_" + str(i),"wb")
			IDFile.write("unknown_" + str(i))
		else:
			outfile = open(sysargv[outfileArg] + "/Files/" + fileName[fileRefID] + fileType[fileRefID],"wb")
			IDFile.write(fileName[fileRefID] + fileType[fileRefID])
		for ii in range(tempSize):
			tempFile.append(SDAT[SDATPos])
			if(calcMD5):
				tempFileString += str(SDAT[SDATPos])
			SDATPos += 1
			outfile.write(tempFile[ii].to_bytes(1,byteorder='little'))
		if(calcMD5):
			fileMD5 = hashlib.md5(tempFileString.encode())
			IDFile.write(";MD5 = " + fileMD5.hexdigest())
		IDFile.write("\n")
	IDFile.close()

if(mode == 2): #Build
	blocks = 4 #temporary, switch to 4 after symbBlock is coded
	if not os.path.exists(sysargv[outfileArg] + "/FileID.txt"):
		print("\nMissing FileID.txt\n")
		quit()
	if not os.path.exists(sysargv[outfileArg] + "/InfoBlock.txt"):
		print("\nMissing InfoBlock.txt\n")
		quit()
	if not os.path.exists(sysargv[outfileArg] + "/SymbBlock.txt"):
		print("\nMissing SymbBlock.txt, proceeding without SymbBlock.\n")
		blocks = 3
	
	IDFile = open(sysargv[outfileArg] + "/FileID.txt", "r")
	thisLine = ""
	numFiles = 0
	done = False
	fileName = []
	while(not done):
		thisLine = IDFile.readline()
		if not thisLine:
			done = True
		thisLine = thisLine.split(";") #ignore anything commented out
		thisLine = thisLine[0]
		thisLine = thisLine.split("\n") #remove newline
		thisLine = thisLine[0]
		if(thisLine != ""):
			fileName.append(thisLine)
			numFiles += 1
	IDFile.close() #file names are stored now

	if(blocks == 4):
		symbFile = open(sysargv[outfileArg] + "/SymbBlock.txt", "r")
		thisLine = ""
		seqSymbNum = 0
		done = False
		seqSymbName = []
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
					seqSymbName.append(thisLine)
					seqSymbNum += 1

		seqarcSymbNum = 0
		seqarcSymbSubNum = 0
		done = False
		seqarcSymbName = []
		seqarcSymbSubCount = [] #keep track of how many sub strings are in each seqarc
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
						seqarcSymbName.append(thisLine[1:])
						seqarcSymbSubNum += 1
						if(seqarcSymbNum == 0):
							print("\nCan't have a sub seqarc before a main one.\n")
							quit()
					else:
						seqarcSymbName.append(thisLine)
						if(seqarcSymbNum > 0):
							seqarcSymbSubCount.append(seqarcSymbSubNum)
						seqarcSymbSubNum = 0
						seqarcSymbNum += 1
		seqarcSymbSubCount.append(seqarcSymbSubNum)

		bankSymbNum = 0
		done = False
		bankSymbName = []
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
					bankSymbName.append(thisLine)
					bankSymbNum += 1

		wavarcSymbNum = 0
		done = False
		wavarcSymbName = []
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
					wavarcSymbName.append(thisLine)
					wavarcSymbNum += 1

		playerSymbNum = 0
		done = False
		playerSymbName = []
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
					playerSymbName.append(thisLine)
					playerSymbNum += 1

		groupSymbNum = 0
		done = False
		groupSymbName = []
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
					groupSymbName.append(thisLine)
					groupSymbNum += 1

		player2SymbNum = 0
		done = False
		player2SymbName = []
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
					player2SymbName.append(thisLine)
					player2SymbNum += 1

		strmSymbNum = 0
		done = False
		strmSymbName = []
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
					strmSymbName.append(thisLine)
					strmSymbNum += 1

		symbFile.close() #symb strings are stored now

	infoFile = open(sysargv[outfileArg] + "/InfoBlock.txt", "r")
	thisLine = ""
	done = False
	SEQNames = []
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
				SEQNames.append(thisLine[0])

	done = False
	SEQARCNames = []
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
				SEQARCNames.append(thisLine[0])

	done = False
	BANKNames = []
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
				BANKNames.append(thisLine[0])

	done = False
	WAVEARCNames = []
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
				WAVEARCNames.append(thisLine[0])

	done = False
	PLAYERNames = []
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
				PLAYERNames.append(thisLine[0])

	done = False
	GROUPNames = []
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
				GROUPNames.append(thisLine[0])

	done = False
	PLAYER2Names = []
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
				PLAYER2Names.append(thisLine[0])

	done = False
	STRMNames = []
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
				STRMNames.append(thisLine[0])
	infoFile.close() #names of the entries of groups are now stored

	infoFile = open(sysargv[outfileArg] + "/InfoBlock.txt", "r")
	thisLine = ""
	seqNum = 0
	done = False
	params = 10
	seqData = [] #SEQ name,fileID,?,bnk,vol,cpr,ppr,ply,?[2]
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
				if(thisLine[0] == "NULL"):
					seqData.append("NULL")
					for i in range(params - 1):
						seqData.append(0)
					seqNum += 1
				else:
					if(len(thisLine) != params):
						print("\nSEQ wrong number of parameters.\n")
						quit()
					thisLine = convert_params(thisLine,[10,0,22,0,0,0,0,0,0])
					for i in range(params):
						seqData.append(thisLine[i])
					seqNum += 1

	seqarcNum = 0
	done = False
	params = 3
	seqarcData = [] #SEQARC name,fileID,?
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
				if(thisLine[0] == "NULL"):
					seqarcData.append("NULL")
					for i in range(params - 1):
						seqarcData.append(0)
					seqarcNum += 1
				else:
					if(len(thisLine) != params):
						print("\nSEQARC wrong number of parameters.\n")
						quit()
					thisLine = convert_params(thisLine,[10,0])
					for i in range(params):
						seqarcData.append(thisLine[i])
					seqarcNum += 1

	bankNum = 0
	done = False
	params = 7
	bankData = [] #BANK name,fileID,?,wa[4]
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
				if(thisLine[0] == "NULL"):
					bankData.append("NULL")
					for i in range(params - 1):
						bankData.append(0)
					bankNum += 1
				else:
					if(len(thisLine) != params):
						print("\nBANK wrong number of parameters.\n")
						quit()
					thisLine = convert_params(thisLine,[10,0,23,23,23,23])
					for i in range(params):
						bankData.append(thisLine[i])
					bankNum += 1

	wavarcNum = 0
	done = False
	params = 3
	wavarcData = [] #WAVARC name,fileID,?
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
				if(thisLine[0] == "NULL"):
					wavarcData.append("NULL")
					for i in range(params - 1):
						wavarcData.append(0)
					wavarcNum += 1
				else:
					if(len(thisLine) != params):
						print("\nWAVARC wrong number of parameters.\n")
						quit()
					thisLine = convert_params(thisLine,[10,0])
					for i in range(params):
						wavarcData.append(thisLine[i])
					wavarcNum += 1

	playerNum = 0
	done = False
	params = 6
	playerData = [] #PLAYER name,?,padding[3],?
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
				if(thisLine[0] == "NULL"):
					playerData.append("NULL")
					for i in range(params - 1):
						playerData.append(0)
					playerNum += 1
				else:
					if(len(thisLine) != params):
						print("\nPLAYER wrong number of parameters.\n")
						quit()
					thisLine = convert_params(thisLine,[0,0,0,0,0])
					for i in range(params):
						playerData.append(thisLine[i])
					playerNum += 1

	groupNum = 0
	done = False
	groupData = [] #GROUP name,count[type,entries]
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
				if(thisLine[0] == "NULL"):
					groupData.append("NULL")
					groupData.append(0)
					groupNum += 1
				else:
					params = (int(thisLine[1]) * 2) + 2
					if(len(thisLine) != params):
						print("\nGROUP wrong number of parameters.\n")
						quit()
					for i in range(params - 1):
						thisLine[i + 1] = int(thisLine[i + 1]) #convert ID to an integer
					for i in range(params):
						groupData.append(thisLine[i])
					groupNum += 1

	player2Num = 0
	done = False
	params = 25
	player2Data = [] #PLAYER2 name,count,v[16],reserved[7]
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
				if(thisLine[0] == "NULL"):
					player2Data.append("NULL")
					for i in range(params - 1):
						player2Data.append(0)
					player2Num += 1
				else:
					if(len(thisLine) != params):
						print("\nPLAYER2 wrong number of parameters.\n")
						quit()
					thisLine = convert_params(thisLine,[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
					for i in range(params):
						player2Data.append(thisLine[i])
					player2Num += 1

	strmNum = 0
	done = False
	params = 11
	strmData = [] #STRM name,fileID,?
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
				if(thisLine[0] == "NULL"):
					strmData.append("NULL")
					for i in range(params - 1):
						strmData.append(0)
					strmNum += 1
				else:
					if(len(thisLine) != params):
						print("\nSTRM wrong number of parameters.\n")
						quit()
					thisLine = convert_params(thisLine,[10,0])
					for i in range(params):
						strmData.append(thisLine[i])
					strmNum += 1
	infoFile.close()
	
	SDAT = []
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

		seqSymbOffset = len(SDAT)
		write_long(symbBlockOffset + 8, seqSymbOffset - symbBlockOffset)
		append_long(seqSymbNum)
		append_reserve(seqSymbNum * 4)

		seqarcSymbOffset = len(SDAT)
		seqarcSymbSubOffset = []
		write_long(symbBlockOffset + 12, seqarcSymbOffset - symbBlockOffset)
		append_long(seqarcSymbNum)
		append_reserve(seqarcSymbNum * 8) #this has sub-groups
		for i in range(seqarcNum):
			write_long((seqarcSymbOffset + 8) + (i * 8), len(SDAT) - symbBlockOffset)
			seqarcSymbSubOffset.append(len(SDAT))
			append_long(seqarcSymbSubCount[i])
			append_reserve(seqarcSymbSubCount[i] * 4)

		bankSymbOffset = len(SDAT)
		write_long(symbBlockOffset + 16, bankSymbOffset - symbBlockOffset)
		append_long(bankSymbNum)
		append_reserve(bankSymbNum * 4)

		wavarcSymbOffset = len(SDAT)
		write_long(symbBlockOffset + 20, wavarcSymbOffset - symbBlockOffset)
		append_long(wavarcSymbNum)
		append_reserve(wavarcSymbNum * 4)

		playerSymbOffset = len(SDAT)
		write_long(symbBlockOffset + 24, playerSymbOffset - symbBlockOffset)
		append_long(playerSymbNum)
		append_reserve(playerSymbNum * 4)

		groupSymbOffset = len(SDAT)
		write_long(symbBlockOffset + 28, groupSymbOffset - symbBlockOffset)
		append_long(groupSymbNum)
		append_reserve(groupSymbNum * 4)

		player2SymbOffset = len(SDAT)
		write_long(symbBlockOffset + 32, player2SymbOffset - symbBlockOffset)
		append_long(player2SymbNum)
		append_reserve(player2SymbNum * 4)

		strmSymbOffset = len(SDAT)
		write_long(symbBlockOffset + 36, strmSymbOffset - symbBlockOffset)
		append_long(strmSymbNum)
		append_reserve(strmSymbNum * 4)

		for i in range(seqSymbNum):
			if(seqSymbName[i] != "NULL"):
				write_long((seqSymbOffset + 4) + (i * 4), len(SDAT) - symbBlockOffset)
				for ii in range(len(seqSymbName[i])):
					append_byte(ord(seqSymbName[i][ii]))
				append_byte(0) #terminate string

		curSeqarc = 0
		for i in range(seqarcSymbNum):
			if(seqarcSymbName[curSeqarc] != "NULL"):
				write_long((seqarcSymbOffset + 4) + (i * 8), len(SDAT) - symbBlockOffset)
				for ii in range(len(seqarcSymbName[curSeqarc])):
					append_byte(ord(seqarcSymbName[curSeqarc][ii]))
				append_byte(0) #terminate string
			curSeqarc += 1
			for subi in range(seqarcSymbSubCount[i]):
				if(seqarcSymbName[curSeqarc] != "NULL"):
					write_long((seqarcSymbSubOffset[i] + 4) + (subi * 4), len(SDAT) - symbBlockOffset)
					for ii in range(len(seqarcSymbName[curSeqarc])):
						append_byte(ord(seqarcSymbName[curSeqarc][ii]))
					append_byte(0) #terminate string
				curSeqarc += 1

		for i in range(bankSymbNum):
			if(bankSymbName[i] != "NULL"):
				write_long((bankSymbOffset + 4) + (i * 4), len(SDAT) - symbBlockOffset)
				for ii in range(len(bankSymbName[i])):
					append_byte(ord(bankSymbName[i][ii]))
				append_byte(0) #terminate string

		for i in range(wavarcSymbNum):
			if(wavarcSymbName[i] != "NULL"):
				write_long((wavarcSymbOffset + 4) + (i * 4), len(SDAT) - symbBlockOffset)
				for ii in range(len(wavarcSymbName[i])):
					append_byte(ord(wavarcSymbName[i][ii]))
				append_byte(0) #terminate string

		for i in range(playerSymbNum):
			if(playerSymbName[i] != "NULL"):
				write_long((playerSymbOffset + 4) + (i * 4), len(SDAT) - symbBlockOffset)
				for ii in range(len(playerSymbName[i])):
					append_byte(ord(playerSymbName[i][ii]))
				append_byte(0) #terminate string

		for i in range(groupSymbNum):
			if(groupSymbName[i] != "NULL"):
				write_long((groupSymbOffset + 4) + (i * 4), len(SDAT) - symbBlockOffset)
				for ii in range(len(groupSymbName[i])):
					append_byte(ord(groupSymbName[i][ii]))
				append_byte(0) #terminate string

		for i in range(player2SymbNum):
			if(player2SymbName[i] != "NULL"):
				write_long((player2SymbOffset + 4) + (i * 4), len(SDAT) - symbBlockOffset)
				for ii in range(len(player2SymbName[i])):
					append_byte(ord(player2SymbName[i][ii]))
				append_byte(0) #terminate string

		for i in range(strmSymbNum):
			if(strmSymbName[i] != "NULL"):
				write_long((strmSymbOffset + 4) + (i * 4), len(SDAT) - symbBlockOffset)
				for ii in range(len(strmSymbName[i])):
					append_byte(ord(strmSymbName[i][ii]))
				append_byte(0) #terminate string

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

	params = 10
	seqOffset = len(SDAT)
	write_long(infoBlockOffset + 8, seqOffset - infoBlockOffset) 
	append_long(seqNum)
	append_reserve(seqNum * 4)
	for i in range(seqNum):
		if(seqData[(i * params)] != "NULL"):
			write_long((seqOffset + 4) + (i * 4), len(SDAT) - infoBlockOffset)
			append_short(seqData[(i * params) + 1])
			append_short(seqData[(i * params) + 2])
			append_short(seqData[(i * params) + 3])
			append_byte(seqData[(i * params) + 4])
			append_byte(seqData[(i * params) + 5])
			append_byte(seqData[(i * params) + 6])
			append_byte(seqData[(i * params) + 7])
			append_byte(seqData[(i * params) + 8])
			append_byte(seqData[(i * params) + 9])

	params = 3
	seqarcOffset = len(SDAT)
	write_long(infoBlockOffset + 12, seqarcOffset - infoBlockOffset) 
	append_long(seqarcNum)
	append_reserve(seqarcNum * 4)
	for i in range(seqarcNum):
		if(seqarcData[(i * params)] != "NULL"):
			write_long((seqarcOffset + 4) + (i * 4), len(SDAT) - infoBlockOffset)
			append_short(seqarcData[(i * params) + 1])
			append_short(seqarcData[(i * params) + 2])

	params = 7
	bankOffset = len(SDAT)
	write_long(infoBlockOffset + 16, bankOffset - infoBlockOffset) 
	append_long(bankNum)
	append_reserve(bankNum * 4)
	for i in range(bankNum):
		if(bankData[(i * params)] != "NULL"):
			write_long((bankOffset + 4) + (i * 4), len(SDAT) - infoBlockOffset)
			append_short(bankData[(i * params) + 1])
			append_short(bankData[(i * params) + 2])
			for ii in range(4):
				append_short(bankData[(i * params) + 3 + ii])

	params = 3
	wavarcOffset = len(SDAT)
	write_long(infoBlockOffset + 20, wavarcOffset - infoBlockOffset) 
	append_long(wavarcNum)
	append_reserve(wavarcNum * 4)
	for i in range(wavarcNum):
		if(wavarcData[(i * params)] != "NULL"):
			write_long((wavarcOffset + 4) + (i * 4), len(SDAT) - infoBlockOffset)
			append_short(wavarcData[(i * params) + 1])
			append_short(wavarcData[(i * params) + 2])

	params = 6
	playerOffset = len(SDAT)
	write_long(infoBlockOffset + 24, playerOffset - infoBlockOffset) 
	append_long(playerNum)
	append_reserve(playerNum * 4)
	for i in range(playerNum):
		if(playerData[(i * params)] != "NULL"):
			write_long((playerOffset + 4) + (i * 4), len(SDAT) - infoBlockOffset)
			append_byte(playerData[(i * params) + 1])
			for ii in range(3):
				append_byte(playerData[(i * params) + 2 + ii])
			append_long(playerData[(i * params) + 5])

	groupOffset = len(SDAT)
	write_long(infoBlockOffset + 28, groupOffset - infoBlockOffset) 
	append_long(groupNum)
	append_reserve(groupNum * 4)
	i = 0
	entry = 0
	while(i < len(groupData)):
		if(groupData[i] != "NULL"):
			write_long((groupOffset + 4) + (entry * 4), len(SDAT) - infoBlockOffset)
			i += 1 #skip the name 
			append_long(groupData[i])
			groupCount = groupData[i]
			i += 1
			for ii in range(groupCount):
				append_long(groupData[i])
				i += 1
				append_long(groupData[i])
				i += 1
		else:
			i += 2 #skip name and 0 for number of entries
		entry += 1

	params = 25
	player2Offset = len(SDAT)
	write_long(infoBlockOffset + 32, player2Offset - infoBlockOffset) 
	append_long(player2Num)
	append_reserve(player2Num * 4)
	for i in range(player2Num):
		if(player2Data[(i * params)] != "NULL"):
			write_long((player2Offset + 4) + (i * 4), len(SDAT) - infoBlockOffset)
			append_byte(player2Data[(i * params) + 1])
			for ii in range(16):
				append_byte(player2Data[(i * params) + 2 + ii])
			for ii in range(7):
				append_byte(player2Data[(i * params) + 18 + ii])

	params = 11
	strmOffset = len(SDAT)
	write_long(infoBlockOffset + 36, strmOffset - infoBlockOffset) 
	append_long(strmNum)
	append_reserve(strmNum * 4)
	for i in range(strmNum):
		if(strmData[(i * params)] != "NULL"):
			write_long((strmOffset + 4) + (i * 4), len(SDAT) - infoBlockOffset)
			append_short(strmData[(i * params) + 1])
			append_short(strmData[(i * params) + 2])
			append_byte(strmData[(i * params) + 3])
			append_byte(strmData[(i * params) + 4])
			append_byte(strmData[(i * params) + 5])
			for ii in range(5):
				append_byte(strmData[(i * params) + 6 + ii])

	write_long(16 + (headeri * 8), infoBlockOffset)
	write_long(20 + (headeri * 8), len(SDAT) - infoBlockOffset)
	headeri += 1
	while((len(SDAT) & 0xFFFFFFFC) != len(SDAT)):
		append_reserve(1) #pad to the nearest 0x04 byte alignment
	write_long(infoBlockOffset + 4, len(SDAT) - infoBlockOffset)

	fatBlockOffset = len(SDAT) #fatBlock
	append_list([ord('F'),ord('A'),ord('T'),0x20]) #Header
	append_long((numFiles * 16) + 12) #fatBlock size
	append_long(numFiles) #number of FAT records
	append_reserve((numFiles * 16))

	write_long(16 + (headeri * 8), fatBlockOffset)
	write_long(20 + (headeri * 8), len(SDAT) - fatBlockOffset)
	headeri += 1
	while((len(SDAT) & 0xFFFFFFFC) != len(SDAT)):
		append_reserve(1) #pad to the nearest 0x04 byte alignment
	write_long(fatBlockOffset + 4, len(SDAT) - fatBlockOffset)

	fileBlockOffset = len(SDAT) #fileBlock
	append_list([ord('F'),ord('I'),ord('L'),ord('E')]) #Header
	append_reserve(4) #fileBlock size
	append_long(numFiles) #number of files
	append_reserve(4) #reserved
	while((len(SDAT) & 0xFFFFFFE0) != len(SDAT)):
		append_reserve(1) #pad to the nearest 0x20 byte alignment

	curFile = 0
	for i in range(len(fileName)):
		if not os.path.exists(sysargv[outfileArg] + "/Files/" + fileName[i]):
			print("\nMissing File:'" + sysargv[outfileArg] + "/Files/" + fileName[i] + "'\n")
			quit()
		curFileLoc = len(SDAT)
		write_long((curFile * 16) + 12 + fatBlockOffset,curFileLoc) #write file pointer to the fatBlock
		tempFile = open(sysargv[outfileArg] + "/Files/" + fileName[i], "rb")
		tFileBuffer = []
		tFileBuffer = tempFile.read()
		tempFile.close()
		write_long((curFile * 16) + 16 + fatBlockOffset,len(tFileBuffer))#write file size to the fatBlock
		for ii in range(len(tFileBuffer)):
			append_byte(tFileBuffer[ii])
		while((len(SDAT) & 0xFFFFFFE0) != len(SDAT)):
			append_reserve(1) #pad to the nearest 0x20 byte alignment
		curFile += 1
	write_long(16 + (headeri * 8), fileBlockOffset)
	write_long(20 + (headeri * 8), len(SDAT) - fileBlockOffset)
	write_long(fileBlockOffset + 4,len(SDAT) - fileBlockOffset) #write fileBlock size
	
	write_long(8, len(SDAT)) #write file size

	outfile = open(sysargv[infileArg],"wb")
	for i in range(len(SDAT)):
		outfile.write(SDAT[i].to_bytes(1,byteorder='little'))
	outfile.close()
