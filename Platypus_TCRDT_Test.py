import sys
import time
import os
from System import Environment
from System import Random
sys.path.append( Environment.CurrentDirectory )
from Platypus_Drive_API import *

test_config_dict = {"pattern_name": "CONCATENATED_SAS_SATA_PRESCRAMBLED_ALL_JITTER_PATTERN,"
									"LOWFREQ_JITTER_PATTERN,"
									"MAJORITY_HIGH_FREQUENCY_PATTERN",
                    "duration": "24:00:00",
                    "segment_count_min": "1",
                    "segment_count_max": "1000",
                    "segment_size_in_blocks_min": "1",
                    "slice_count": "8",
                    "pattern_change_period": "01:00:00",
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
    for device in GetGUIDByType(scheduler, "System_Backend", "local"):
        ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))

# Gather drive information
drives = Drives(scheduler, test_config_dict)

drives.get_logs()

while True:
    
    # Random Write #################################################################
    
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "random_write", drive, 86700,
            Param("pattern_name","none","string"),
			Param("pattern_custom", "B5 B5 B5 B5 B5 B5 B5 B5 7E 7E 7E 7E 7E 7E 7E 7E", "string"),
            Param("slice_count","1","dec"))
    EndConcurrentTest(scheduler)

    # Log Errors ###################################################################

    drives.get_logs()

    # Verify ########################################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "sequential_verify", drive, drives.drive_config_dict[drive]["timeout"],
            Param("duration", "00:00:00", "duration"),
            Param("loop_count", "1", "dec"),
            Param("verification_size_in_blocks_max",drives.drive_config_dict[drive]["verification_size"], "hex"))
    EndConcurrentTest(scheduler)
    
    # Log Errors ###################################################################

    drives.get_logs()

    # Random Write Verify ##########################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "random_write_verify", drive, 86700,
            Param("slice_count","1","dec"))
    EndConcurrentTest(scheduler)

    # Log Errors ###################################################################

    drives.get_logs()

    # Sequential Read/Write loop ##############################################################
    start_time = time.clock()	
    while (time.clock() - start_time) < 172800:
        BeginConcurrentTest(scheduler)
        for drive in drives.drive_list_single_path:
            ExecuteTestWithTimeout(scheduler, "sequential_read", drive, drives.drive_config_dict[drive]["timeout"],
                Param("duration", "00:00:00", "duration"),
                Param("loop_count", "1", "dec"))
        EndConcurrentTest(scheduler)
        BeginConcurrentTest(scheduler)
        for drive in drives.drive_list_single_path:
            ExecuteTestWithTimeout(scheduler, "sequential_write", drive, drives.drive_config_dict[drive]["timeout"],
                Param("duration", "00:00:00", "duration"),
                Param("pattern_custom", "A0 A0 A0 A0 A0 A0 A0 A0 0A 0A 0A 0A 0A 0A 0A 0A", "string"),
                Param("loop_count", "1", "dec"))
        EndConcurrentTest(scheduler)
    
    # Log Errors ###################################################################

    drives.get_logs()
    
    # Verify ########################################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "sequential_verify", drive, drives.drive_config_dict[drive]["timeout"],
            Param("duration", "00:00:00", "duration"),
            Param("loop_count", "1", "dec"),
            Param("verification_size_in_blocks_max",drives.drive_config_dict[drive]["verification_size"], "hex"))
    EndConcurrentTest(scheduler)

    # Log Errors ###################################################################

    drives.get_logs()

    # Random Read ##################################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "random_read", drive, 86700)
    EndConcurrentTest(scheduler)

    # Log Errors ###################################################################

    drives.get_logs()

    # Butterfly Seek ###############################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "butterfly_seek", drive, 86700,
			Param("duration","12:00:00","duration"),
            Param("inc_val", "1", "hex"),
            Param("xfer_type", drives.drive_config_dict[drive]["seek_type"], "string"),
			Param("transfer_size_in_blocks_min", "1", "hex"),
			Param("transfer_size_in_blocks_max", "1", "hex"))
    EndConcurrentTest(scheduler)

    # Log Errors ###################################################################

    drives.get_logs()

    # Random Write Read ############################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "random_write_read", drive, 86700,
            Param("data_compare_option", "true", "bool"),
            Param("segment_count_min", "1", "dec"),
            Param("segment_count_max", "1", "dec"))
    EndConcurrentTest(scheduler)

    # Log Errors ###################################################################

    drives.get_logs()    
    
    # Verify ########################################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "sequential_verify", drive, drives.drive_config_dict[drive]["timeout"],
            Param("duration", "00:00:00", "duration"),
            Param("loop_count", "1", "dec"),
            Param("verification_size_in_blocks_max",drives.drive_config_dict[drive]["verification_size"], "hex"))
    EndConcurrentTest(scheduler)
    
    # Log Errors ###################################################################

    drives.get_logs()

    ################################################################################
