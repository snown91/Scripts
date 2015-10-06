'''
AriesHC E6 Log Dump to Binary File

Usage
AriesHC SATA drives adopt a SAS-like E6 SMART log format which inncludes multiple logs
in one dump file. Drive log lengths are roughly 16MB. Files are generaged using the 
drives Serial Number, as well as the date of the dump, and are appended with a .bin 
(ie Serial_DD_MM_YY.bin). Files are placed in C:\RDT\SMART

HGST specified the E6 Dump command in the following format:

Feature: 00A2
Sector Count: XXXX
LBA 47-32: 1F00
LBA 31-16: OFFSET
LBA 15-00: 0071
Device: 40
Command 7-0: FE

Using the scsi_ata_pass_through_16 command in Platypus, the above translates to the following format:

command: FE
Device: 40
Feature: 00A2
Lba_low: XX71
Lba_mid: 0000
Lba_high: 1FXX
Sector_count: XXXX

Here, the offset corresponds to lba_low(15:8) + lba_high(7:0). So, if the offset is set to FF or lower, 
fill lba_low(15:8) with the desired offset and set lba_high(7:0) with 00. Similarly, for any offsets
greater than FF blocks, fill lba_low(15:8) with 00 and lba_high(7:0) with the desired offset. Sector count
and offset must be set to the same value.

In this script implementation, the log is dumped in a series of 8 chunks, with the sector count set to 
0x1000 and the offset incrementing from 0x000 to 0x7000. This will yield an 0x8000 sector dump. 

'''
import sys
import time
import os
from System import Environment
from System import Random
sys.path.append( Environment.CurrentDirectory )
from Platypus_Drive_API import *
import binascii

# Discover Backend Must ALWAYS be true unless otherwise debugging
discover_backend = False

#Upload error_manager.xml Rulebook
FileTransfer(scheduler, "C:\\RDT\\Scripts\\error_manager.xml", "/platypus/policy/backend/", "local", {"Protocol":"FTP","Mode":"LAN"})

# Discover all drives in system
if discover_backend:
    for device in GetGUIDByType(scheduler, "System_Backend", "local"):
        ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))
        
test_config_dict = {}

drives = Drives(scheduler,test_config_dict)

# Report Characteristics #######################################################
drive_dict = {}

BeginConcurrentTest(scheduler)
for drive in drives.drive_list_single_path:
        drive_dict[drive] = ExecuteTestWithTimeout(scheduler, "report_characteristics", drive, 60)
EndConcurrentTest(scheduler)

# Smart Dump (E6) ##########################################################

def getLogLength(data):
    output_string = binascii.b2a_hex(binascii.a2b_base64(ExtractData(data, "//data_in")))
    output_list = [output_string[i:i + 2] for i in range(0,len(output_string), 2)]
    log_length_list = output_list[4:8]
    log_length = ''.join(log_length_list)
    return log_length

def generateFIS(log_length):
    fislist = []
    int_log = int('0x' + log_length, 16)
    num_of_sectors = (int_log / 512) + 1
   
    main_transfer = num_of_sectors / 4096
    residual_transfer = num_of_sectors % 4096
    byte_overflow = (num_of_sectors * 512) - int_log
    
    for offset in range(main_transfer):
        lba_low = hex(offset)[2:] + "0"

        fislist.append((lba_low, "1000","200000",0)) #lba_low, sector_count, allocation_length, byte_overflow
    
    sector_count = hex(residual_transfer)[2:].zfill(4)
    final_main_transfer = hex(main_transfer)[2:] + "0"
    allocation_length = hex(residual_transfer * 512)[2:]

    fislist.append((final_main_transfer, sector_count, allocation_length, byte_overflow))

    return fislist


    
date = time.strftime("%Y_%m_%d")
path = 'c:\\RDT\\SMART\\' + date
if not os.path.exists(path):
    os.makedirs(path)
    
for drive in drives.drive_list_single_path:  
    drive_serial = GetTestOutput(drive_dict[drive], "//characteristic_data/serial_number" ).strip()    
    filename_bin = drive_serial + "_" + date +".bin"
    f = open('c:\\RDT\\SMART\\' + date + '\\' + filename_bin,"wb")

    mode_list = ["10","14"]
    
    for mode in mode_list:

        BeginConcurrentTest(scheduler)
        results = ExecuteTestWithTimeout(scheduler, "scsi_ata_pass_through_16", drive, 300,
                Param("allocation_length", "200", "hex"),
                Param("command", "fe", "hex"),
                Param("device", "00", "hex"),
                Param("extend", "true", "bool"),
                Param("byte_block", "true", "bool"),
                Param("features", "00a2", "hex"),
                Param("lba_low", "0071", "hex"),
                Param("lba_mid", "0000", "hex"),
                Param("lba_high", mode + "00", "hex"),
                Param("sector_count", "1", "hex"))
        EndConcurrentTest(scheduler)
        
        log_length = getLogLength(results)
        fislist = generateFIS(log_length)

        for lba_low, sector_count, allocation_length, byte_overflow in fislist:
            BeginConcurrentTest(scheduler)
            results = ExecuteTestWithTimeout(scheduler, "scsi_ata_pass_through_16", drive, 300,
                Param("allocation_length", allocation_length, "hex"),
                Param("command", "fe", "hex"),
                Param("device", "00", "hex"),
                Param("extend", "true", "bool"),
                Param("byte_block", "true", "bool"),
                Param("features", "00a2", "hex"),
                Param("lba_low", lba_low + "71", "hex"),
                Param("lba_mid", "0000", "hex"),
                Param("lba_high", mode + "00", "hex"),
                Param("sector_count", sector_count, "hex"))
            EndConcurrentTest(scheduler)

            residual = int(allocation_length,16) - byte_overflow
            binresults = binascii.a2b_base64(GetTestOutput(results,"//data_in"))[:residual]
            f.write(binresults)
    f.flush()
    f.close()  
 
