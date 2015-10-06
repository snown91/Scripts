import sys
import time
import os
from System import Environment
from System import Random
sys.path.append( Environment.CurrentDirectory )
from Platypus_Drive_API import *
import binascii
import base64

test_config_dict = {}

# Discover Backend Must ALWAYS be true unless otherwise debugging
discover_backend = True

#Upload error_manager.xml Rulebook
FileTransfer(scheduler, "C:\\RDT\\Scripts\\error_manager.xml", "/platypus/policy/backend/", "local", {"Protocol":"FTP","Mode":"LAN"})

# Discover all drives in system
if discover_backend:
    for device in GetGUIDByType(scheduler, "System_Backend", "local"):
        ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))

drives = Drives(scheduler, test_config_dict)
def getLogLength(data):
    output_string = binascii.b2a_hex(binascii.a2b_base64(ExtractData(data, "//data_in")))
    output_list = [output_string[i:i + 2] for i in range(0,len(output_string), 2)]
    log_length_list = output_list[4:8]
    log_length = ''.join(log_length_list)
    return log_length
    
def generateCDB(mode, log_length):
    cdb_list = []
    hex_log = int('0x' + log_length, 16)
    main_transfer = hex(hex_log / 0x100000)
    residual_transfer = hex(hex_log % 0x100000)

    for offset_raw in range(int(main_transfer, 16)):
        offset = hex(offset_raw)[2:].zfill(1) + '00000'
        raw_cdb = 'e600'+ mode + offset + '10000000'
        formatted_cdb = " ".join(raw_cdb[i:i+2] for i in range(0, len(raw_cdb), 2))
        cdb_list.append((formatted_cdb,"100000"))
        
    raw_cdb = 'e600' + mode + main_transfer[2:].zfill(1) + '00000' + residual_transfer[2:].zfill(6) + '00'
    formatted_cdb = " ".join(raw_cdb[i:i+2] for i in range(0, len(raw_cdb), 2))
    cdb_list.append((formatted_cdb, residual_transfer))

    return cdb_list

date = time.strftime("%Y_%m_%d")
path = 'c:\\RDT\\SMART\\' + date
if not os.path.exists(path):
    os.makedirs(path)
                
for drive in drives.drive_list_single_path:
    if drives.drive_info_dict[drive].info_items["protocol"] == "SAS":
        drive_serial = drives.drive_info_dict[drive].info_items["serial_number"].strip()
        offset_string = '0'    
        filename_bin = drive_serial + "_" + date +".bin"
        f = open('c:\\RDT\\SMART\\' + date + '\\' + filename_bin,"wb")

        mode_list = ["10","14"]
        
        for mode in mode_list:
            results = ExecuteTestWithTimeout(scheduler, "scsi_user_defined", drive, 300,
                Param("allocation_length", "08", "hex"),
                Param("cdb", "E6 00 " + mode + " 00 00 00 00 00 08 00", "string"))
                
            if HasErrorOrTimeout(results):
                break
                
            else:
                log_length = getLogLength(results)
                cdb_list = generateCDB(mode, log_length)

                for cdb, allocation_length in cdb_list:
                    results = ExecuteTestWithTimeout(scheduler, "scsi_user_defined", drive, 300,
                        Param("allocation_length", allocation_length, "hex"),
                        Param("cdb", cdb, "string")) 
                    binresults = binascii.a2b_base64(GetTestOutput(results,"//data_in"))
                    f.write(binresults)
        f.flush()
        f.close()
