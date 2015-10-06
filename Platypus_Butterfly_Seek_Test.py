import sys
import time
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
    for device in GetGUIDByType(scheduler, "System_Backend","local"):
        ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))
    EndConcurrentTest(scheduler)

# Gather drive information
drives = Drives(scheduler, test_config_dict)

drives.get_logs()

################################################################################
#################################### RDT #######################################
################################################################################

    
disk_params = [("1","0"),("10","0"),("10","9")] #lba range in to specify IO access as [(Full Disk), (OD), (ID)]    

for chunk_count,chunk_number in disk_params: #Loop over FD, OD, and ID

    #Set LBA Range
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTest(scheduler, "set_lba_range", drive,
            Param("chunk_count", chunk_count, "dec"),
            Param("chunk_number", chunk_number, "dec"))
    EndConcurrentTest(scheduler)

    for day in range(4): #loops seek seeks for 4 days
        # Log Errors ###################################################################

        drives.get_logs()
        
        # Butterfly Seek ###############################################################
        BeginConcurrentTest(scheduler)
        for drive in drives.drive_list_single_path:
            ExecuteTestWithTimeout(scheduler, "butterfly_seek", drive, 86700,
                Param("inc_val", "1", "hex"),
                Param("xfer_type", drives.drive_config_dict[drive]["seek_type"], "string"),
                Param("transfer_size_in_blocks_min", "1", "hex"),
                Param("transfer_size_in_blocks_max", "1", "hex"))
        EndConcurrentTest(scheduler)
    
    # Log Errors ###################################################################

    drives.get_logs()
    
    # Sequential Read ##############################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "sequential_read", drive, drives.drive_config_dict[drive]["timeout"],
                Param("duration", "00:00:00", "duration"),
                Param("loop_count", "1", "dec"),
                Param("slice_count", "1", "dec"))
    EndConcurrentTest(scheduler)
    
    # Log Errors ###################################################################

    drives.get_logs()
    
    # Random Write Read ############################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "random_write_read", drive, 3800,
            Param("duration", "01:00:00", "duration"),
            Param("data_compare_option", "true", "bool"),
            Param("pattern_name", "none", "string"),
            Param("pattern_custom", "DE AD BE EF", "string"),
            Param("segment_count_min", "1", "dec"),
            Param("segment_count_max", "1", "dec"))
    EndConcurrentTest(scheduler)
    

    for day in range(3): #loops write seeks for 3 days
    
        # Log Errors ###################################################################

        drives.get_logs()
        
        # Butterfly Seek ###############################################################
        BeginConcurrentTest(scheduler)
        for drive in drives.drive_list_single_path:
            ExecuteTestWithTimeout(scheduler, "butterfly_seek", drive, 86700,
                Param("inc_val", "1", "hex"),
                Param("xfer_type", "write", "string"),
                Param("transfer_size_in_blocks_min", "1", "hex"),
                Param("transfer_size_in_blocks_max", "1", "hex"))
        EndConcurrentTest(scheduler)
    
    # Log Errors ###################################################################

    drives.get_logs()
    
    # Sequential Read ##############################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "sequential_read", drive, drives.drive_config_dict[drive]["timeout"],
                Param("duration", "00:00:00", "duration"),
                Param("loop_count", "1", "dec"),
                Param("slice_count", "1", "dec"),
                Param("pattern_custom", "DE AD BE EF", "string"))
    EndConcurrentTest(scheduler)
    
    # Log Errors ###################################################################

    drives.get_logs()
    
    # Random Write Read ############################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "random_write_read", drive, 3800,
            Param("duration", "01:00:00", "duration"),
            Param("data_compare_option", "true", "bool"),
            Param("pattern_name", "none", "string"),
            Param("pattern_custom", "DE AD BE EF", "string"),
            Param("segment_count_min", "1", "dec"),
            Param("segment_count_max", "1", "dec"))
    EndConcurrentTest(scheduler)
    

    for day in range(3): #loops read seeks for 3 days
        # Log Errors ###################################################################

        drives.get_logs()
        
        # Butterfly Seek ###############################################################
        BeginConcurrentTest(scheduler)
        for drive in drives.drive_list_single_path:
            ExecuteTestWithTimeout(scheduler, "butterfly_seek", drive, 86700,
                Param("inc_val", "1", "hex"),
                Param("xfer_type", "read", "string"),
                Param("transfer_size_in_blocks_min", "1", "hex"),
                Param("transfer_size_in_blocks_max", "1", "hex"))
        EndConcurrentTest(scheduler)
    
    # Log Errors ###################################################################

    drives.get_logs()
    
    # Sequential Read ##############################################################

    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "sequential_read", drive, drives.drive_config_dict[drive]["timeout"],
            Param("duration", "00:00:00", "duration"),
            Param("loop_count", "1", "dec"),
            Param("slice_count", "1", "dec"),
            Param("pattern_custom", "DE AD BE EF", "string"))
    EndConcurrentTest(scheduler)
    
    # Log Errors ###################################################################

    drives.get_logs()
    
    # Random Write Read ############################################################

    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "random_write_read", drive, 3800,
            Param("duration", "01:00:00", "duration"),
            Param("data_compare_option", "true", "bool"),
            Param("pattern_name", "none", "string"),
            Param("pattern_custom", "DE AD BE EF", "string"),
            Param("segment_count_min", "1", "dec"),
            Param("segment_count_max", "1", "dec"))
    EndConcurrentTest(scheduler)

    # Log Errors ###################################################################

    drives.get_logs()
