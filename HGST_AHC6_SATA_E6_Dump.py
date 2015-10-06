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
discover_backend = True

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

date = time.strftime("%Y_%m_%d")
path = 'c:\\RDT\\SMART\\' + date
if not os.path.exists(path):
    os.makedirs(path)
    
for drive in drives.drive_list_single_path:  
    drive_serial = GetTestOutput(drive_dict[drive], "//characteristic_data/serial_number" ).strip()	
    filename_bin = drive_serial + "_" + date +".bin"
    f = open('c:\\RDT\\SMART\\' + date + '\\' + filename_bin,"wb")

    lba_low_list = ["0071","1071","2071","3071","4071","5071","6071","7071"]
    
    for lba_low in lba_low_list:
        BeginConcurrentTest(scheduler)
        results = ExecuteTestWithTimeout(scheduler, "scsi_ata_pass_through_16", drive, 300,
                Param("allocation_length", "200000", "hex"),
                Param("command", "fe", "hex"),
                Param("device", "40", "hex"),
                Param("extend", "true", "bool"),
                Param("byte_block", "true", "bool"),
                Param("features", "00a2", "hex"),
                Param("lba_low", lba_low, "hex"),
                Param("lba_mid", "0000", "hex"),
                Param("lba_high", "1f00", "hex"),
                Param("sector_count", "1000", "hex"))
        EndConcurrentTest(scheduler)
        binresults = binascii.a2b_base64(GetTestOutput(results,"//data_in"))
        f.write(binresults)
    f.close()	
