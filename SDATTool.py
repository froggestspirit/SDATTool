#SDAT-Tool by FroggestSpirit
version = "0.0.1"
#Unpacks and builds SDAT files
#Make backups, this can overwrite files without confirmation

import sys
import os
import math

def read_long(pos):
	global SDAT
	return (SDAT[pos + 3] * 0x1000000) + (SDAT[pos + 2] * 0x10000) + (SDAT[pos + 1] * 0x100) + SDAT[pos]
	
def read_short(pos):
	global SDAT
	return (SDAT[pos + 1] * 0x100) + SDAT[pos]
	
def get_params(list):
	global SDATPos
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
	return retString

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
	print("Usage: "+sysargv[0]+" input [mode] [output] [flags]\nMode:\n\t-b\tBuild SDAT\n\t-u\tUnpack SDAT\n\t-h\tShow this help message\n")
	sys.exit()

if(mode == 1): #Unpack
	if not os.path.exists(sysargv[outfileArg]):
		os.makedirs(sysargv[outfileArg])
	infile = open(sysargv[infileArg], "rb")
	global SDAT
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
		if(blocks == 4 and i < len(SEQNames)):
			fileType.append(".sseq")
			fileNameID.append(read_short(SDATPos))
			fileName.append(SEQNames[i])
			outfile.write(SEQNames[i] + "," + get_params([2,2,2,1,1,1,1,1,1]) + "\n")
		else:
			outfile.write("NULL," + get_params([2,2,2,1,1,1,1,1,1]) + "\n")
	outfile.write("}\n\n")

	SDATPos = SEQARCOffset
	outfile.write("SEQARC(fileID,?){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(SEQARCOffset + 4 + (i * 4)) + infoOffset
		if(blocks == 4 and i < len(SEQARCNames)):
			fileType.append(".ssar")
			fileNameID.append(read_short(SDATPos))
			fileName.append(SEQARCNames[i])
			outfile.write(SEQARCNames[i] + "," + get_params([2,2]) + "\n")
		else:
			outfile.write("NULL," + get_params([2,2]) + "\n")
	outfile.write("}\n\n")

	SDATPos = BANKOffset
	outfile.write("BANK(fileID,?,wa[4]){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(BANKOffset + 4 + (i * 4)) + infoOffset
		if(blocks == 4 and i < len(BANKNames)):
			fileType.append(".sbnk")
			fileNameID.append(read_short(SDATPos))
			fileName.append(BANKNames[i])
			outfile.write(BANKNames[i] + "," + get_params([2,2,2,2,2,2]) + "\n")
		else:
			outfile.write("NULL," + get_params([2,2,2,2,2,2]) + "\n")
	outfile.write("}\n\n")

	SDATPos = WAVEARCOffset
	outfile.write("WAVEARC(fileID,?){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(WAVEARCOffset + 4 + (i * 4)) + infoOffset
		if(blocks == 4 and i < len(WAVEARCNames)):
			fileType.append(".swar")
			fileNameID.append(read_short(SDATPos))
			fileName.append(WAVEARCNames[i])
			outfile.write(WAVEARCNames[i] + "," + get_params([2,2]) + "\n")
		else:
			outfile.write("NULL," + get_params([2,2]) + "\n")
	outfile.write("}\n\n")

	SDATPos = PLAYEROffset
	outfile.write("PLAYER(?,padding[3],?){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(PLAYEROffset + 4 + (i * 4)) + infoOffset
		if(blocks == 4 and i < len(PLAYERNames)):
			outfile.write(PLAYERNames[i] + "," + get_params([1,1,1,1,4]) + "\n")
		else:
			outfile.write("NULL," + get_params([1,1,1,1,4]) + "\n")
	outfile.write("}\n\n")

	SDATPos = GROUPOffset
	outfile.write("GROUP(count[type,entries]){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(GROUPOffset + 4 + (i * 4)) + infoOffset
		count = read_long(SDATPos)
		if(blocks == 4 and i < len(GROUPNames)):
			outfile.write(GROUPNames[i] + "," + get_params([4]))
		else:
			outfile.write("NULL," + get_params([4]))
		for ii in range(count):
				outfile.write("," + get_params([4,4]))
		outfile.write("\n")
	outfile.write("}\n\n")

	SDATPos = PLAYER2Offset
	outfile.write("PLAYER2(count,v[16],reserved[7]){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(PLAYER2Offset + 4 + (i * 4)) + infoOffset
		if(blocks == 4 and i < len(PLAYER2Names)):
			outfile.write(PLAYER2Names[i] + "," + get_params([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]) + "\n")
		else:
			outfile.write("NULL," + get_params([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]) + "\n")
	outfile.write("}\n\n")

	SDATPos = STRMOffset
	outfile.write("STRM(fileID,?,vol,pri,ply,reserved[5]){\n")
	entries = read_long(SDATPos)
	for i in range(entries):
		SDATPos = read_long(STRMOffset + 4 + (i * 4)) + infoOffset
		if(blocks == 4 and i < len(STRMNames)):
			fileType.append(".strm")
			fileNameID.append(read_short(SDATPos))
			fileName.append(STRMNames[i])
			outfile.write(STRMNames[i] + "," + get_params([2,2,1,1,1,1,1,1,1,1]) + "\n")
		else:
			outfile.write("NULL," + get_params([2,2,1,1,1,1,1,1,1,1]) + "\n")
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
		done = False
		if(blocks == 4):
			fileRefID = 0
			while(fileNameID[fileRefID] != i and not done):
				fileRefID += 1
				if(fileRefID >= len(fileNameID)):
					fileRefID = -1
					done = True
		else:
			fileRefID = -1
		if(fileRefID == -1):
			outfile = open(sysargv[outfileArg] + "/Files/" + str(i),"wb")
			IDFile.write(str(i) + "," + str(i) + "\n")
		else:
			outfile = open(sysargv[outfileArg] + "/Files/" + fileName[fileRefID] + fileType[fileRefID],"wb")
			IDFile.write(str(i) + "," + fileName[fileRefID] + fileType[fileRefID] + "\n")
		for ii in range(tempSize):
			tempFile.append(SDAT[SDATPos])
			SDATPos += 1
			outfile.write(tempFile[ii].to_bytes(1,byteorder='little'))
		outfile.close()
	IDFile.close()