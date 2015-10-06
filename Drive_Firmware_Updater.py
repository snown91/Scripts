import sys
import time
from System import Environment
from System import Random
sys.path.append( Environment.CurrentDirectory )
from Platypus_Drive_API import *

####PUT THE DRIVE DIRMWARE FILE HERE########
fw_name = ""

test_config_dict = {}

discover_backend = True

#upload firmware file
FileTransfer(scheduler, "C:\\RDT\\Scripts\\Firmware\\" + fw_name, "/platypus/firmware", "local", {"Protocol":"FTP","Mode":"LAN"})

# Discover all drives in system
if discover_backend:
    for device in GetGUIDByType(scheduler, "System_Backend", "local"):
        ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))

# Gather drive information
drives = Drives(scheduler, test_config_dict)

all_firmware_guids = GetGUIDByType(scheduler,'Firmware','local')

BeginConcurrentTest(scheduler)
for drive in drives.drive_list_single_path:
    for firmware_guid in GetIntersection(QueryChildrenGUIDByGUID(scheduler,drive),all_firmware_guids):
        if firmware_guid not in GetGUIDByType(scheduler,'Drive_Paddle_card','local'):
            ExecuteTestWithTimeout(scheduler, "update_firmware", firmware_guid, 300,
                                    Param("image_path", "/platypus/firmware", "string"),
                                    Param("image_name", fw_name, "string"))
EndConcurrentTest(scheduler)

# Report Characteristics #######################################################
BeginConcurrentTest(scheduler)
for drive in drives.drive_list_single_path:
    ExecuteTestWithTimeout(scheduler, "report_characteristics", drive, 60)
EndConcurrentTest(scheduler)