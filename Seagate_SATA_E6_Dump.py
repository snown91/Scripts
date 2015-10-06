import sys
import time
import os
from System import Environment
from System import Random
sys.path.append( Environment.CurrentDirectory )
from Platypus_Drive_API import *
import binascii

# Discover Backend Must ALWAYS be true unless otherwise debugging
discover_backend = True

#Upload error_manager.xml Rulebook
FileTransfer(scheduler, "C:\\RDT\\Scripts\\error_manager.xml", "/platypus/policy/backend/", "local", {"Protocol":"FTP","Mode":"LAN"})

# Discover all drives in system
if discover_backend:
    for device in GetGUIDByType(scheduler, "System_Backend", "local"):
        ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))


# Gather drive information
drives = Drives(scheduler, test_config_dict)

# Report Characteristics #######################################################
drive_dict = {}
BeginConcurrentTest(scheduler)
for drive in drives.drive_list_single_path:
    drive_dict[drive] = ExecuteTestWithTimeout(scheduler, "report_characteristics", drive, 60)
EndConcurrentTest(scheduler)

# Smart Dump (E6) ##########################################################
date = time.strftime("%d_%m_%y")
path = 'c:\\RDT\\SMART\\' + date
if not os.path.exists(path):
    os.makedirs(path)


PAGES_PER_PARSE = 255



def CreateIndexStartList(PageCount, PagesPerParse):
    IndexStartList = [] #IndexStartList is a list containing the first index in each parse
    pageCounter = 0
    while(pageCounter < PageCount):
        IndexStartList.append(hex(pageCounter))
        pageCounter += PagesPerParse
        
    return IndexStartList

def GetA2PageCount(Object):
    output_string = binascii.b2a_hex(binascii.a2b_base64(ExtractData(Object, "//data_in")))
    output_list = [output_string[i:i + 4] for i in range(0, len(output_string), 4)]
    for index, two_byte in enumerate(output_list):
        bytes = [two_byte[i:i + 2] for i in range(0, len(two_byte), 2)]
        address = hex(index) # Decimal to Hex
        pages = int(bytes[1] + bytes[0], 16) # Hex to Decimal
        if(address == hex(162)):
            return pages

def GetPageCount(PageIndex, DrivePageCount, PagesPerParse):
    PageIndex = int(PageIndex, 16)
    if(DrivePageCount - PageIndex >= 255):
        return 'FF'
    else:
        return str(hex(DrivePageCount - PageIndex))

for drive in drives.drive_list_single_path:
    drive_serial = GetTestOutput(drive_dict[drive], "//characteristic_data/serial_number" ).strip()	
    filename_bin = drive_serial + "_" + date +".SM2"
    
    f = open('c:\\RDT\\SMART\\' + date + '\\' + filename_bin,"wb")

    BeginConcurrentTest(scheduler)
    DriveLogPageInformation = ExecuteTestWithTimeout(scheduler, "sata_log_test", drive, 60,
        Param("count", "1", "hex"),
        Param("features", "0", "hex"), #Feature 0D SATA READ DATA
        Param("log_address", "0", "hex"),
        Param("log_page", "0", "hex"),
        Param("smart", "false", "bool"),
        Param("write", "false", "bool"))
    EndConcurrentTest(scheduler)
    
    DrivePageCount = GetA2PageCount(DriveLogPageInformation)
    IndexStartList = CreateIndexStartList(DrivePageCount, PAGES_PER_PARSE)
    
    for pageIndex in IndexStartList:
        BeginConcurrentTest(scheduler)
        results = ExecuteTestWithTimeout(scheduler, "sata_log_test", drive, 300,
                Param("count", GetPageCount(pageIndex, DrivePageCount, PAGES_PER_PARSE), "hex"),
                Param("data_out", "", "string"),
                Param("features", "0", "hex"),
                Param("log_address", "A2", "hex"),
                Param("log_page", pageIndex, "hex"),
                Param("smart", "false", "bool"),
                Param("write", "false", "bool"))
        EndConcurrentTest(scheduler)
        
        binresults = binascii.a2b_base64(GetTestOutput(results,"//data_in"))
        f.write(binresults)
    f.close()
        
        
