#From Draxx182.
#Using HeartlessSeph's file hact.chp template as base (modified for my mapping on newer games)
#Using Sutando's Python Binary Reader for easy access reads

#Imports
import math
import json
import sys
import os
import shutil
import time
from pathlib import Path
from collections import defaultdict
from binary_reader import BinaryReader

def tree(): #Makes a tree :troll:
    def the_tree():
        return defaultdict(the_tree)
    return the_tree()

def export_json(target_path, filename, data): #Writes a json to a certain directory
    jsonFile = json.dumps(data, ensure_ascii=False, indent=2)
    jsonPath = target_path / (filename+ '.json')
    jsonPath.write_text(jsonFile)

hactDict = tree()

if (len(sys.argv) <= 1): #Catch anyone who's not drag and dropping >:c
    print('Drag and drop hact.chp for this script to work.')
    print('Have a readily available \"talk_param.bin.json\" (needs to be named like this and extracted from reARMP)')
    print('Ensure that talk_param.bin.json is in the same directory as hact.chp')
    input("Press ENTER to exit... ")
else: #If argument is valid, move onto checking for file types
    propertyPath = sys.argv[1]
    if (propertyPath.endswith(".chp")):
        #Binary Reader Conditions Settings
        file = open(propertyPath, 'rb')
        rd = BinaryReader(file.read())
        rd.set_endian(False)
        new_path = Path(os.path.dirname(propertyPath))
        talk_param = Path(os.path.join(new_path, 'talk_param.bin.json'))

        #Checks to see if talk_param.bin.json exists (if it's in the same directory, basically).
        if(talk_param.is_file() == False):
            print("No \"talk_param.bin.json\" detected (needs to be named exactly like this and extracted from reARMP).")
            print('Ensure that talk_param.bin.json is in the same directory as hact.chp')
            input("Press ENTER to exit...")
            sys.exit()
        with open(talk_param, 'rb') as t:
            param_json = json.loads(t.read())
        nameOfFile = os.path.basename(os.path.normpath(propertyPath))
        nameOfFile = nameOfFile[:-4]

        #File Header Variables
        #Don't need to mess with the header as much, though we will need to compensate for the file size.
        hactDict["FileHeader"]["Magic"] = rd.read_str(4)
        hactDict["FileHeader"]["Endianess"] = rd.read_uint16()
        hactDict["FileHeader"]["Unk1"] = rd.read_uint16()
        hactDict["FileHeader"]["File Version"] = rd.read_uint32()
        filesize = rd.read_uint32()
        
        #Hact Variables
        #These are set at the bottom of the .chp file. There is a 4 byte filler inbetween the number of hacts.
        rd.seek(filesize - 16)
        numOfHacts = rd.read_uint32() #The number of hacts there are
        rd.read_uint32() #filler
        pointerToHactTable = rd.read_uint32() #Pointer to where the hact table is

        #Hact Data
        rd.seek(pointerToHactTable)
        #Variables to keep track of every node in the file
        hTableAnchor = 0
        aTableAnchor = 0
        aTableAnchor2 = 0
        pTableAnchor = 0
        stringList = [] #List of strings stored and used in the chp

        #Start of the hact loops.
        for j in range(numOfHacts):
            #Header of Hact
            pointerToHact = rd.read_uint32()
            rd.read_uint32() #filler
            hTableAnchor = rd.pos()

            #Name of Hact
            rd.seek(pointerToHact)
            #This ID points to the name in talk_param
            nameID = rd.read_uint32()
            name = list(param_json[str(nameID)].keys())[0] #Nabbed this one from Seph

            #Meat of the Data
            hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Index ID"] = rd.read_uint32() #Idk what index does tbh lol
            pointerToActorTable = rd.read_uint32()
            rd.read_uint32() #filler
            hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["HAct Type"] = rd.read_uint32() #Idk what type does tbh lol
            rd.read_uint32() #filler
            rd.read_uint32() #filler
            numOfActors = rd.read_uint32() #Number of Actors there are

            #These floats (and uint, apparently) seem only prominent at the end (judging by LJ's HACT CHP)
            hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Unk 0"] = rd.read_uint32()
            hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Unk 1"] = rd.read_float()
            hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Unk 2"] = rd.read_float()
            hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Unk 3"] = rd.read_float()
            hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Unk 4"] = rd.read_float()
            hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Unk 5"] = rd.read_float()

            #Actor Data
            if (pointerToHact != pointerToActorTable):
                rd.seek(pointerToActorTable)
                for i in range(numOfActors):
                    #Actor Header
                    pointerToActor = rd.read_uint32()
                    rd.read_uint32() #filler
                    aTableAnchor = rd.pos()

                    #Actor Data
                    rd.seek(pointerToActor)
                    pointerToName = rd.read_uint32()
                    rd.read_uint32() #filler
                    aTableAnchor2 = rd.pos()
                    rd.seek(pointerToName)
                    nameActor = rd.read_str()
                    rd.seek(aTableAnchor2)

                    #Actor Properties
                    pointerToPropertyTable = rd.read_uint32()
                    rd.read_uint32() #filler
                    hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Target Table"]["Target "+str(i + 1)]["Target Name"] = nameActor
                    stringList.append(nameActor)
                    hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Target Table"]["Target "+str(i + 1)]["Target Type"] = rd.read_uint32()
                    rd.read_uint32() #filler
                    numOfProperty = rd.read_uint32()
                    rd.read_uint32() #filler
                    rd.seek(pointerToPropertyTable)
                    
                    if (numOfProperty == 0):
                        hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Target Table"]["Target "+str(i + 1)]["Properties Table"] = "null"
                    #Property Table
                    for c in range(numOfProperty):
                        pointerToProperty = rd.read_uint32()
                        rd.read_uint32() #filler
                        pTableAnchor = rd.pos()
                        rd.seek(pointerToProperty + 8)
                        propertyType = rd.read_uint32()
                        hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Target Table"]["Target "+str(i + 1)]["Properties Table"]["Property "+str(c+1)]["Property Type"] = propertyType
                        rd.seek(pointerToProperty)
                        hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Target Table"]["Target "+str(i + 1)]["Properties Table"]["Property "+str(c+1)]["Unk Byte 1"] = rd.read_uint8()
                        hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Target Table"]["Target "+str(i + 1)]["Properties Table"]["Property "+str(c+1)]["Unk Byte 2"] = rd.read_uint8()
                        hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Target Table"]["Target "+str(i + 1)]["Properties Table"]["Property "+str(c+1)]["Unk Byte 3"] = rd.read_uint8()
                        hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Target Table"]["Target "+str(i + 1)]["Properties Table"]["Property "+str(c+1)]["Unk Byte 4"] = rd.read_uint8()

                        if (propertyType == 41):
                            hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Target Table"]["Target "+str(i + 1)]["Properties Table"]["Property "+str(c+1)]["Unk Byte 5"] = rd.read_uint8()
                            hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Target Table"]["Target "+str(i + 1)]["Properties Table"]["Property "+str(c+1)]["Unk Byte 6"] = rd.read_uint8()
                            hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Target Table"]["Target "+str(i + 1)]["Properties Table"]["Property "+str(c+1)]["Unk Byte 7"] = rd.read_uint8()
                            hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Target Table"]["Target "+str(i + 1)]["Properties Table"]["Property "+str(c+1)]["Unk Byte 8"] = rd.read_uint8()
                        rd.seek(pTableAnchor)
                    rd.seek(aTableAnchor)
            else:
                hactDict["HAct Table"]["Heat Action "+str(j+1)][name]["Target Table"] = "null"
            rd.seek(hTableAnchor)
        hactDict["Actor Name Table"] = list(dict.fromkeys(stringList))
        export_json(new_path, nameOfFile, hactDict) #Exports hact.chp
        file.close()

    elif (propertyPath.endswith(".json")):
        #Binary Writer Settings
        #Loads in file, then creates a new Binary Writer object
        file = open(propertyPath, 'rb')
        actionDict = json.loads(file.read())
        wr = BinaryReader(file.read())
        wr.set_endian(False)
        find_path = Path(os.path.dirname(propertyPath))
        talk_param = Path(os.path.join(find_path, 'talk_param.bin.json'))

        #Checks to see if talk_param.bin.json exists (if it's in the same directory, basically).
        if(talk_param.is_file() == False):
            print("No \"talk_param.bin.json\" detected (needs to be named exactly like this and extracted from reARMP).")
            print('Ensure that talk_param.bin.json is in the same directory as hact.chp')
            input("Press ENTER to exit...")
            sys.exit()
        with open(talk_param, 'rb') as t:
            param_json = json.loads(t.read())
        #Indexes talk param for naming purposes
        keyNames = list(param_json.keys())
        valueNames = list(param_json.values())
        paramTree = tree()

        #Loops through keynames to index in param tree
        for key in range(len(keyNames)):
            #Very sore to look at, but this will work.
            try:
                paramTree[list(valueNames[key].keys())[0]] = keyNames[key]
            except:
                continue

        #File Header Variables
        #Again, don't need to mess with them much besides file size at the end.
        actionDict = list(actionDict.values())
        headerDict = list(actionDict[0].values())
        wr.write_str(headerDict[0])
        wr.write_uint16(headerDict[1])
        wr.write_uint16(headerDict[2])
        wr.write_uint32(headerDict[3])
        wr.write_uint32(0) #Placeholder for file size

        #String Table Variables
        #Iterates through the used string table and writes
        stringTree = tree()
        stringDict = actionDict[2]
        wr.write_str("", null=True)
        for string in stringDict:
            stringTree[string] = wr.pos()
            wr.write_str(string, null=True)
        #wr.write_str("coyote_dogfood", null=True) #This is for LJ replication lol

        #Offset with CC byte to maintain 4-byte order
        ccByte = wr.pos() % 4
        for item in range(4-ccByte):
            wr.write_uint8(204)
        #This probably won't do anything, but I'm going to put it in anyways
        #for replication purposes.
        wr.write_uint8(204)
        wr.write_uint8(204)
        wr.write_uint8(204)
        wr.write_uint8(204)

        #HAct Table Variables
        #Variables to keep track of every node in the file
        hTableAnchor = 0
        h2TableAnchor = 0
        aTableAnchor = 0
        aTableAnchor2 = 0
        pTableAnchor = 0
        hactDict = actionDict[1].values()
        listOfHactPointers = []

        for hact in hactDict:
            unpackedHact = list(hact.values())
            name = list(hact.keys())
            hactData = list(unpackedHact[0].values())

            #Actor Table
            #(Has to be before the actual data)
            actors = []
            if (hactData[8] != "null"):
                for actor in (list(hactData[8].values())):
                    actorData = list(actor.values())
                    actorName = actorData[0]
                    actorType = actorData[1]
                    propertiesTable = actorData[2]

                    #Property Table
                    pointersOfPointerTable = []
                    if (propertiesTable != "null"):
                        #Property Data Bytes
                        for prop in (list(propertiesTable.values())):
                            pointersOfPointerTable.append(wr.pos())
                            propertyData = list(prop.values())
                            propertyType = propertyData[0]
                            propertyByte1 = propertyData[1]
                            propertyByte2 = propertyData[2]
                            propertyByte3 = propertyData[3]
                            propertyByte4 = propertyData[4]

                            #Actual Data Bytes of property
                            wr.write_uint8(propertyByte1)
                            wr.write_uint8(propertyByte2)
                            wr.write_uint8(propertyByte3)
                            wr.write_uint8(propertyByte4)
                            if (propertyType == 41): #Extra data structure for property 41
                                propertyByte5 = propertyData[5]
                                propertyByte6 = propertyData[6]
                                propertyByte7 = propertyData[7]
                                propertyByte8 = propertyData[8]

                                wr.write_uint8(propertyByte5)
                                wr.write_uint8(propertyByte6)
                                wr.write_uint8(propertyByte7)
                                wr.write_uint8(propertyByte8)
                            else:
                                wr.write_uint32(0) #filler

                            #Property type
                            wr.write_uint32(propertyType)
                            wr.write_uint32(0) #filler
                        
                        #Property Pointers
                        pointerToPointerOfPropetryPointers = wr.pos()
                        for pointer in pointersOfPointerTable:
                            wr.write_uint32(pointer)
                            wr.write_uint32(0) #filler
                        
                    #Writes Actor Variables
                    actorPosition = wr.pos()
                    actors.append(actorPosition)
                    wr.write_uint32(stringTree[actorName]) #Writes pointer to the string table
                    wr.write_uint32(0) #filler

                    #Actor Data + Property Pointers
                    if (propertiesTable == "null"):
                        wr.write_uint32(actorPosition)
                    else:
                        wr.write_uint32(pointerToPointerOfPropetryPointers) #Writes pointer to the property pointers
                    wr.write_uint32(0) #filler
                    wr.write_uint32(actorType) #Actor Type Write
                    wr.write_uint32(0) #filler
                    if (propertiesTable != "null"):
                        wr.write_uint32(len(list(propertiesTable.values()))) #Writes Size of Property Table
                    else:
                        wr.write_uint32(0)
                    wr.write_uint32(0) #filler

            pointerToPropertiesPointer = wr.pos()
            #Finally, writes pointer to where the Actor Data is
            if (hactData[8] != "null"):
                for actor in actors:
                    wr.write_uint32(actor)
                    wr.write_uint32(0) #filler

            listOfHactPointers.append(wr.pos())
            #Meat of HAct Data
            #This is ugly, but it will do for now.
            wr.write_uint32(int(paramTree[name[0]])) #Name ID Index
            wr.write_uint32(hactData[0]) #HAct Index
            wr.write_uint32(pointerToPropertiesPointer) #Pointer to Actor Table
            wr.write_uint32(0) #Filler
            wr.write_uint32(hactData[1])
            wr.write_uint32(0) #Filler
            wr.write_uint32(0) #Filler
            if (hactData[8] != "null"):
                wr.write_uint32(len(list(hactData[8].values()))) #Number of Actors
            else:
                wr.write_uint32(0)
            #Unks
            wr.write_uint32(hactData[2])
            wr.write_float(hactData[3])
            wr.write_float(hactData[4])
            wr.write_float(hactData[5])
            wr.write_float(hactData[6])
            wr.write_float(hactData[7])

        #Pointer Table
        pointerToPointerTable = wr.pos()
        for pointer in listOfHactPointers:
            wr.write_uint32(pointer)
            wr.write_uint32(0)
        
        #Write bytes at end of the file
        wr.write_uint32(len(hactDict))
        wr.write_uint32(0)
        wr.write_uint32(pointerToPointerTable)
        wr.write_uint32(0)

        #Changes filesize of the header
        wr.seek(12)
        wr.write_uint32(wr.size())

        if propertyPath.endswith('.json'): #Cuts .json out of file_path
            new_path = propertyPath[:-5]
            with open(new_path+" new.chp", 'wb') as f:
                f.write(wr.buffer())
        else:
            with open(propertyPath+".chp", 'wb') as f:
                f.write(wr.buffer())
            new_path = propertyPath
        file.close()
