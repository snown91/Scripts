import sys
import time
import os
from System import Environment
from System import Random
sys.path.append( Environment.CurrentDirectory )
from Platypus_Drive_API import *
import binascii

test_config_dict = {"pattern_name": "none",
                    "duration": "12:00:00",
                    "segment_count_min": "1",
                    "segment_count_max": "1000",
                    "segment_size_in_blocks_min": "1",
                    "slice_count": "8",
                    "pattern_change_period": "00:00:00",
					"chunk_count":"1",
					"chunk_number":"0"}

# Discover Backend Must ALWAYS be true unless otherwise debugging
discover_backend = True

#Check to make sure we have the correct platypus version
nondrive = NonDrive(scheduler)
nondrive.platypus_check(scheduler)
nondrive.echidna_check(scheduler)

#Upload error_manager.xml Rulebook
FileTransfer(scheduler, "C:\\RDT\\Scripts\\error_manager.xml", "/platypus/policy/backend/", "local", {"Protocol":"FTP","Mode":"LAN"})

# Discover all drives in system
if discover_backend:
    BeginConcurrentTest(scheduler)
    for device in GetGUIDByType(scheduler, "System_Backend", "local"):
        ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))
	EndConcurrentTest(scheduler)

# Gather drive information
drives = Drives(scheduler, test_config_dict)

drives.get_logs()

# Headwear Test Sequence ###########################################################
while True: #loops indefinitely

    #set time in secs when write same loop will end
    endtime = int(time.time()) + 604800 #set to 604800 secs for a week
    
    while time.time() <= endtime: #While loop ends after set amount of time
        BeginConcurrentTest(scheduler)
        for drive in drives.drive_list_single_path:
            ExecuteTestWithTimeout(scheduler, "write_same", drive, drives.drive_config_dict[drive]["timeout"],
                Param("data_out", drives.drive_config_dict[drive]["data_out_string"], "string"))
        EndConcurrentTest(scheduler)

    # Log Errors ###################################################################
    drives.get_logs()
    
    # Sequential Read ##########################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "sequential_read", drive, drives.drive_config_dict[drive]["timeout"],
            Param("duration", "00:00:00", "duration"),
            Param("loop_count", "1", "dec"),
            Param("pattern_custom", "DE AD BE EF", "string"),
            Param("data_compare_option", "true", "bool"))
    EndConcurrentTest(scheduler)
    
    # Log Errors ###################################################################
    drives.get_logs()
    
    # Random Write Read ########################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "random_write_read", drive, 10800,
            Param("pattern_name","INCREMENTAL_PATTERN","string"),
            Param("duration", "02:00:00", "duration"))
    EndConcurrentTest(scheduler)
	
    # Log Errors ###################################################################
	
    drives.get_logs()

    # Sequential Write #########################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "sequential_write", drive, 10800,
            Param("duration", "02:00:00", "duration"),
            Param("pattern_custom", "A0 A0 A0 A0 A0 A0 A0 A0 0A 0A 0A 0A 0A 0A 0A 0A", "string"),
            Param("loop_count", "1000", "dec"))
    EndConcurrentTest(scheduler)
	
    # Log Errors ###################################################################
    drives.get_logs()

    # Sequential Read ##########################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "sequential_read", drive, 10800,
            Param("duration", "02:00:00", "duration"),
            Param("pattern_custom", "A0 A0 A0 A0 A0 A0 A0 A0 0A 0A 0A 0A 0A 0A 0A 0A", "string"),
            Param("loop_count", "1000", "dec"))
    EndConcurrentTest(scheduler)
	
    # Log Errors ###################################################################
    drives.get_logs()

# END ##########################################################################

















