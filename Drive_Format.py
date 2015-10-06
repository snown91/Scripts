import sys
import time
import os
import base64
from System import Environment
from System import Random
sys.path.append( Environment.CurrentDirectory )
from Platypus_Drive_API import *
import binascii

#PUT YOUR BLOCK SIZE HERE LIKE "520" OR "4160". MUST BE IN DECIMAL
format = "520"

test_config_dict = {}

# Discover Backend Must ALWAYS be true unless otherwise debugging
discover_backend = True

#Upload error_manager.xml Rulebook
FileTransfer(scheduler, "C:\\RDT\\Scripts\\error_manager.xml", "/platypus/policy/backend/", "local", {"Protocol":"FTP","Mode":"LAN"})

# Discover all drives in system
if discover_backend:
    for device in LocalLogicalDiscoveryByType(scheduler, "System_Backend"):
        ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))

# Gather drive information
drives = Drives(scheduler, test_config_dict)

BeginConcurrentTest(scheduler)
for drive in drives.drive_list_single_path:
    ExecuteTestWithTimeout(scheduler, "format", drive, 86400,
                            Param("plist", "true", "bool"),
                            Param("glist", "true", "bool"),
                            Param("block_length", format, "dec"))
EndConcurrentTest(scheduler)