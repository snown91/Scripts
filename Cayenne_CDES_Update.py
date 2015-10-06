import sys
import time
from System import Environment
from System import Random
sys.path.append( Environment.CurrentDirectory )
from Platypus_Drive_API import *

boot = "boot_mips.bin"
cdef = "cdef.bin"
cdef_dual = "cdef_dual.bin"
istr = "istr.bin"
cdes_rom = "cdes_rom.bin"

discover_backend = True

#upload firmware file
FileTransfer(scheduler, "C:\\RDT\\Scripts\\Firmware\\CDES-2\\" + boot, "/platypus/firmware", "local", {"Protocol":"FTP","Mode":"LAN"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\\Firmware\\CDES-2\\" + cdef, "/platypus/firmware", "local", {"Protocol":"FTP","Mode":"LAN"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\\Firmware\\CDES-2\\" + cdef_dual, "/platypus/firmware", "local", {"Protocol":"FTP","Mode":"LAN"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\\Firmware\\CDES-2\\" + istr, "/platypus/firmware", "local", {"Protocol":"FTP","Mode":"LAN"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\\Firmware\\CDES-2\\" + cdes_rom, "/platypus/firmware", "local", {"Protocol":"FTP","Mode":"LAN"})


# Discover all devices in system
if discover_backend:
        for device in LocalLogicalDiscoveryByType(scheduler, "System_Backend"):
                        ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))


io_expanders = LocalLogicalDiscoveryByType(scheduler, "Local_Master_ESES_Expander")
drive_expanders = LocalLogicalDiscoveryByType(scheduler, "Local_Slave_ESES_Expander")

for io_expander in io_expanders:
    ExecuteTestWithTimeout(scheduler, "update_firmware", io_expander, 600,
        Param("image_path", "/platypus/firmware", "string"),
        Param("image_name", boot, "string"))
        
    ExecuteTestWithTimeout(scheduler, "update_firmware", io_expander, 600,
        Param("image_path", "/platypus/firmware", "string"),
        Param("image_name", cdef, "string"))

    ExecuteTestWithTimeout(scheduler, "update_firmware", io_expander, 600,
        Param("image_path", "/platypus/firmware", "string"),
        Param("image_name", istr, "string"))
        
    ExecuteTestWithTimeout(scheduler, "update_firmware", io_expander, 600,
        Param("image_path", "/platypus/firmware", "string"),
        Param("image_name", cdes_rom, "string"))
        
for drive_expander in drive_expanders:
    ExecuteTestWithTimeout(scheduler, "update_firmware", drive_expander, 600,
        Param("image_path", "/platypus/firmware", "string"),
        Param("image_name", boot, "string"))
        
    ExecuteTestWithTimeout(scheduler, "update_firmware", drive_expander, 600,
        Param("image_path", "/platypus/firmware", "string"),
        Param("image_name", cdef, "string"))

    ExecuteTestWithTimeout(scheduler, "update_firmware", drive_expander, 600,
        Param("image_path", "/platypus/firmware", "string"),
        Param("image_name", istr, "string"))
        
    ExecuteTestWithTimeout(scheduler, "update_firmware", drive_expander, 600,
        Param("image_path", "/platypus/firmware", "string"),
        Param("image_name", cdes_rom, "string"))

