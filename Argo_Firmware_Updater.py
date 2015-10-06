import sys
import time
from System import Environment
from System import Random
sys.path.append( Environment.CurrentDirectory )
from Platypus_Drive_API import *

####PUT THE DRIVE DIRMWARE FILE HERE
bios = "argonautbios.bin"
post = "argonautpost.bin"
fwbundle = "fwbundle.bin"

discover_backend = True

#upload firmware file
FileTransfer(scheduler, "C:\\RDT\\Scripts\\Firmware\\Argonaut_SP_FW\\" + bios, "/platypus/firmware", "local", {"Protocol":"FTP","Mode":"LAN"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\\Firmware\\Argonaut_SP_FW\\" + post, "/platypus/firmware", "local", {"Protocol":"FTP","Mode":"LAN"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\\Firmware\\Argonaut_SP_FW\\" + fwbundle, "/platypus/firmware", "local", {"Protocol":"FTP","Mode":"LAN"})


bios_device = GetGUIDByType(scheduler, "BIOS", "local")[0]
post_device = GetGUIDByType(scheduler, "POST", "local")[0]
fwbundle_device = GetGUIDByName(scheduler, "Firmware Bundle", "local")[0]

ExecuteTestWithTimeout(scheduler, "update_firmware", bios_device, 600,
    Param("image_path", "/platypus/firmware","string"),
    Param("image_name", bios, "string"))
    
ExecuteTestWithTimeout(scheduler, "update_firmware", post_device, 600,
    Param("image_path", "/platypus/firmware","string"),
    Param("image_name", post, "string"))
    
ExecuteTestWithTimeout(scheduler, "update_firmware", fwbundle_device, 600,
    Param("image_path", "/platypus/firmware","string"),
    Param("image_name", fwbundle, "string"))
    
