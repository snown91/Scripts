import sys
import time
import csv
import os
from System import Environment
from System import Random
sys.path.append( Environment.CurrentDirectory )
from Platypus_Drive_API import *

# Discover Backend Must ALWAYS be true unless otherwise debugging
discover_backend = True

#Check to make sure we have the correct platypus version
nondrive = NonDrive(scheduler)
nondrive.platypus_check(scheduler)
nondrive.echidna_check(scheduler)

# Discover all drives in system
if discover_backend:
    for device in LocalLogicalDiscoveryByType(scheduler, "System_Backend"):
        ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))

test_config_dict = {}

# Gather drive information
drives = Drives(scheduler, test_config_dict)

BeginConcurrentTest(scheduler)
for drive in drives.drive_list_single_path:
    ExecuteTest(scheduler, "wait_unit_ready", drive,
        Param("do_not_report_filter","06/[0-9A-Fa-f]{2}/[0-9A-Fa-f]{2}","string"),
        Param("duration","00:01:00","duration") )
EndConcurrentTest(scheduler)

drives.mode_page_check()

# END ##########################################################################

















