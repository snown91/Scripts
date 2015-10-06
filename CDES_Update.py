import sys
import time
from System import Environment
from System import Random
sys.path.append( Environment.CurrentDirectory )
from Platypus_Drive_API import *

cdes = "cdes_0152.bin"

discover_backend = True

#upload firmware file
FileTransfer(scheduler, "C:\\RDT\\Scripts\\Firmware\\" + cdes, "/platypus/firmware", "local", {"Protocol":"FTP","Mode":"LAN"})


# Discover all devices in system
if discover_backend:
        for device in LocalLogicalDiscoveryByType(scheduler, "System_Backend"):
                        ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))


expanders = LocalLogicalDiscoveryByType(scheduler, "Local_Master_ESES_Expander")

for expander in expanders:
    ExecuteTestWithTimeout(scheduler, "update_firmware", expander, 600,
        Param("image_path", "/platypus/firmware", "string"),
        Param("image_name", cdes, "string"))
        

        
