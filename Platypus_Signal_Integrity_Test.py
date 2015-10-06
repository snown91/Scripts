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
                    "pattern_change_period": "00:00:00"}
					
#Check to make sure we have the correct platypus version
nondrive = NonDrive(scheduler)
nondrive.platypus_check(scheduler)
nondrive.echidna_check(scheduler)

FileTransfer(scheduler, "C:\\RDT\\Scripts\\error_manager.xml", "/platypus/policy/backend/", "local", {"Protocol":"FTP","Mode":"LAN"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\\error_manager.xml", "/platypus/policy/backend/", "peer", {"Protocol":"FTP","Mode":"LAN"})

def discover_system(scheduler, test_config_dict):
    # Discover all drives in system

    discover_backend = True
    
    if discover_backend:
        BeginConcurrentTest(scheduler)
        for device in GetGUIDByType(scheduler,"System_Backend","local"):
            ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))
        for device in GetGUIDByType(scheduler,"System_Backend","peer"):
            ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))
        EndConcurrentTest(scheduler)
        
    drives = Drives(scheduler, test_config_dict)

    #Create a list of local DAEs
    daes = []
    dae_list = GetGUIDByType(scheduler,"ESES_DAE","local") + GetGUIDByType(scheduler,"ESES_DAE","peer")
    
    return  dae_list, drives

drive_rates = ["sdrvrate -d all -r 6G","sdrvrate -d all -r 3G"] #Loop pulls in 6G code, then 3G code

data_patterns = ["LOWFREQ_JITTER_PATTERN", "MAJORITY_HIGH_FREQUENCY_PATTERN", "CONCATENATED_SAS_SATA_PRESCRAMBLED_ALL_JITTER_PATTERN"]

for drive_rate in drive_rates:

    dae_list, drives = discover_system(scheduler, test_config_dict)
    
    time.sleep(10)
    
    # Set Link Speed ################################################################
    BeginConcurrentTest(scheduler)
    for dae in dae_list:
        ExecuteTestWithTimeout(scheduler, "send_command_server_command", dae, 60,
            Param("command", drive_rate, "string"),
            Param("waiting_time_for_cmd_completion", "500", "dec"))
    EndConcurrentTest(scheduler)
	
    time.sleep(10)
    
    dae_list, drives = discover_system(scheduler, test_config_dict)
    
    # Reset Phy Error Counter #######################################################
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "wait_unit_ready", drive, 60,
            Param("do_not_report_filter","06/[0-9A-Fa-f]{2}/[0-9A-Fa-f]{2}","string"))
    for drive in drives.drive_list_single_path:
        ExecuteTestWithTimeout(scheduler, "wait_unit_ready", drive, 60,
            Param("do_not_report_filter","06/[0-9A-Fa-f]{2}/[0-9A-Fa-f]{2}","string"))
    EndConcurrentTest(scheduler)

    # Random Write Read Loop Over Patterns ##########################################

    for data_pattern in data_patterns:
        
		#Get Logs ###################################################################
        drives.get_logs()
        
		#Random Write Read ##########################################################
        BeginConcurrentTest(scheduler)
        for drive in drives.drive_list_single_path:
            ExecuteTestWithTimeout(scheduler, "random_write_read", drive, 205200,
                Param("duration", "56:00:00", "duration"),
                Param("pattern_name", data_pattern, "string"))
        EndConcurrentTest(scheduler)
    
    
    
    
    
    
    
    
    

        

