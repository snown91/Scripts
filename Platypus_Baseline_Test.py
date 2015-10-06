import sys
import time
from System import Environment
from System import Random
sys.path.append( Environment.CurrentDirectory )
from Platypus_Drive_API import *

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
    for device in LocalLogicalDiscoveryByType(scheduler, "System_Backend"):
        ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))
	EndConcurrentTest(scheduler)

# Gather drive information
drives = Drives(scheduler, test_config_dict)

# Get Logs #####################################################################

drives.get_logs()

# Baseline Write Same ##########################################################

BeginConcurrentTest(scheduler)
for drive in drives.drive_list_single_path:
    ExecuteTestWithTimeout(scheduler, "write_same", drive, drives.drive_config_dict[drive]["timeout"],
					Param("wrprotect", "0", "hex"),
					Param("pbdata", "false", "bool"),
					Param("number_of_blocks", "0", "hex"),
					Param("logical_block_address", "0", "hex"),
					Param("lbdata", "false", "bool"),
					Param("data_out", drives.drive_config_dict[drive]["data_out_string"], "string"),
					Param("group_number", "0", "hex"))
EndConcurrentTest(scheduler)

# Get Logs #####################################################################

drives.get_logs()

# 1 Pass Sequential Read #######################################################

BeginConcurrentTest(scheduler)
for drive in drives.drive_list_single_path:
	ExecuteTestWithTimeout(scheduler, "sequential_read", drive, drives.drive_config_dict[drive]["timeout"],
                    Param("pattern_custom", "DE AD BE EF", "string"),
					Param("duration", "00:00:00", "duration"),
					Param("loop_count", "1", "dec"))
EndConcurrentTest(scheduler)

# Get Logs #####################################################################

drives.get_logs()

