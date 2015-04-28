
import ROOT as r
import string
import sys, getopt


# ======================================================
# parsing command line arguments
# ======================================================
RunNum = ''
TrkPartition = ''
refTrkPartition = ''

myopts, args = getopt.getopt(sys.argv[1:], "r:p:f:")

# o == option, a == argument passed to the o
for o, a in myopts:
    if o == '-r':
        RunNum = a
    elif o == '-p':
        TrkPartition = a
    elif o == '-f':
        refTrkPartition = a
    else:
        print("Usage: %s -r run_number -p tracker_partition -f ref_tracker_partition" % sys.argv[0])

# Display input and output file names passed as the args
print ("Run number: %s, Tracker partition: %s, ref partition %s" % (RunNum, TrkPartition, refTrkPartition))


# ======================================================
# Sub-detectors info and save to different lists
# ======================================================
def getSubDetID(detid):
	Numdetid = string.atoi(detid)
	sub = (Numdetid>>25)&0x7
	return sub

SubDetNames = {
		3:"TIB",
		4:"TID",
		5:"TOB",
		6:"TEC"
		}

# ======================================================
# Configurables
# ======================================================
outFileName = "out_%s_%s.root" % (TrkPartition, RunNum)

# ======================================================
# File keys to specify files
# ======================================================
fileKeys = ["ISHA","idAddress","idTemp","mapping"]
baseDir = "/afs/cern.ch/user/y/yduh/CalibrationScan/txt/2015/"
fileNames = {
		"ISHA":"ishavfsScan_sane3sigmas.txt.%s_%s" % (TrkPartition, RunNum),
		"idAddress":"2_id_address.txt",
		"idTemp":"3_id_Temp.txt",
		"mapping":"4_Temp_ISHA_VFS_%s.txt" % refTrkPartition
		#"mapping":"4_Temp_ISHA_VFS_TEC.txt"
		#"mapping":"4_Temp_ISHA_VFS_TOB.txt"
		}

# ======================================================
# Data format to store information
# ======================================================
outFile = r.TFile(outFileName,"RECREATE")
allData = {}
ISHAHists = {}
VFSHists = {}
for SubDetID,SubDetName in SubDetNames.iteritems():
    ISHAHists[SubDetID] = r.TH1D("ISHA_%s"%SubDetName," ; #Delta ISHA %s ; Entry"%SubDetName,201,-100.5,100.5)
    VFSHists[SubDetID] = r.TH1D("VFS_%s"%SubDetName," ; #Delta VFS %s ; Entry"%SubDetName,201,-100.5,100.5)
    ISHAHists[SubDetID].SetTitle("Run %s"%RunNum)
    VFSHists[SubDetID].SetTitle("Run %s"%RunNum)

# ======================================================
# Add basedir to fileNames, because I am lazy
# ======================================================
for fileKey in fileKeys:
	fileNames[fileKey] = baseDir+fileNames[fileKey]


# ======================================================
# Read columns from files and store in allData
# ======================================================
mappingList = []
ISHAValues = {}
VFSValues = {}
for fileKey in fileKeys:
	allData[fileKey] = {}
	inputLines = open(fileNames[fileKey],"r").readlines()
	for lineNumber,line in enumerate(inputLines):
		if line != "\n":
			if fileKey == "idAddress":
				modifiedLineKey = ".".join(line.split()[1].split(".")[1:])
				allData[fileKey][modifiedLineKey] = line.split()[0]
			elif fileKey == "idTemp":
				allData[fileKey][line.split()[0]] = line.split()[1]
			elif fileKey == "mapping":
				allData[fileKey][line.split()[0]] = line.split()[1:]
				mappingList.append(int(line.split()[0]))
			else:
				tempDataList = line.split()
				allData[fileKey][lineNumber] = (".".join( tempDataList[:5]  ), tempDataList[-2], tempDataList[-1] )

				truncAddress = ".".join( tempDataList[:4] )

				if truncAddress not in ISHAValues:
					ISHAValues[truncAddress] = []
				ISHAValues[truncAddress].append(int(tempDataList[-2]))

				if truncAddress not in VFSValues:
					VFSValues[truncAddress] = []
				VFSValues[truncAddress].append(int(tempDataList[-1]))

# ======================================================
# Get the final ISHA and VFS for each column
# ======================================================
finalISHAs = {}
finalVFSs = {}
for lineNumber,datum in allData["ISHA"].iteritems():
	truncAddress = ".".join(datum[0].split()[0].split(".")[:-1])
	if truncAddress in finalISHAs or truncAddress in finalVFSs: continue
	if datum[0].split(".")[2][0] != "0":
		addressForIDAddress = ".".join(datum[0].split(".")[:-1])
	else:
		tempList = datum[0].split(".")
		addressForIDAddress = ".".join([ tempList[0], tempList[1], tempList[2],tempList[3][1:],tempList[4]  ])
	if addressForIDAddress in allData["idAddress"]:
		addressForIDTemp = allData["idAddress"][addressForIDAddress]
		if addressForIDTemp in allData["idTemp"]:
			# print addressForIDAddress,allData["idAddress"][addressForIDAddress],allData["idTemp"][allData["idAddress"][addressForIDAddress]]
			subDetID = getSubDetID(addressForIDTemp)
			mappingAddress = min(mappingList, key=lambda x:abs(x-float(allData["idTemp"][allData["idAddress"][addressForIDAddress]])))
			finalISHA, finalVFS = allData["mapping"][str(mappingAddress)]
			# print finalISHA, finalVFS
			finalISHAs[truncAddress] = (int(finalISHA),subDetID)
			finalVFSs[truncAddress] = (int(finalVFS),subDetID)

for key,initialISHAValues in ISHAValues.iteritems():
	for initialISHAValue in initialISHAValues:
		if key in finalISHAs:
			ISHAHists[finalISHAs[key][1]].Fill(initialISHAValue-finalISHAs[key][0])

for key,initialVFSValues in VFSValues.iteritems():
	for initialVFSValue in initialVFSValues:
		if key in finalVFSs:
			VFSHists[finalVFSs[key][1]].Fill(initialVFSValue-finalVFSs[key][0])

for key,Hist in ISHAHists.iteritems():
	Hist.Write()

for key,Hist in VFSHists.iteritems():
	Hist.Write()


outFile.Close()



