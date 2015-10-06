FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_bios_Megatron.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_post_MEGATRON.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_bmc_main.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_bmc_BBLOCK.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_ssp_megatron.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_pci-switch0_megatronB_plx.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_pci-switch1_megatronB_plx.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_pci-switch2_megatronB_plx.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_pci-switch3_megatronB_plx.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_eth-fw_megatron_broadcom.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_ps_octane_0802.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_cmd-app_100d815pin.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_cmd-bb_100d815pin.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_cmd-cfg_100d815pin.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_cmd-app_44pin.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_cmd-bb_44pin.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_cmd-cfg_44pin.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_uefi_fw_volume.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_mgmt_mcu_akula.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_cmd-app_100pin.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_cmd-bb_100pin.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_cmd-cfg_100pin.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_serdes_Megatron.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\emc_pmc_sas_moonlite.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
FileTransfer(scheduler, "C:\\RDT\\Scripts\Firmware\Megatron_SP_FW\spve_0208.bin","/platypus/firmware","local",{"Protocol":"FTP","Mode":"AUTO"})
device = LogicalDiscovery(scheduler, "CDI")
nSP = len(device)

def Check_Device(ExpectedDeviceNumber,Fun,*arg):   #Will not check the number of devices if ExpectedDeviceNumber is -1
	device = Fun(*arg)
	if len(device) == 0:
		VirtualTest(arg[0], "DeviceNotFound", True, "["+arg[1]+"]",  arg[1] + " is NOT found!" )
		return
	if ExpectedDeviceNumber == -1: #we don't care or don't know the number of devices
		return
	if len(device) != ExpectedDeviceNumber:
		VirtualTest(arg[0], "DeviceNotFound", True, "["+arg[1]+"]",  arg[1] + ": Number of the device is wrong!" )
	
Check_Device(nSP,LogicalDiscovery,scheduler, "BIOS")
BeginConcurrentTest(scheduler)
for device in LogicalDiscovery(scheduler, "BIOS"):
	ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_bios_Megatron.bin", "string"))
	ExecuteTest(scheduler, "update_firmware", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_bios_Megatron.bin", "string"), Param("force", "yes", "string"))
EndConcurrentTest(scheduler)

Check_Device(nSP,LogicalDiscovery,scheduler, "POST")
BeginConcurrentTest(scheduler)
for device in LogicalDiscovery(scheduler, "POST"):
	ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_post_MEGATRON.bin", "string"))
	ExecuteTest(scheduler, "update_firmware", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_post_MEGATRON.bin", "string"), Param("force", "yes", "string"))
EndConcurrentTest(scheduler)

Check_Device(nSP,LogicalDiscovery,scheduler, "BMC")
BeginConcurrentTest(scheduler)
for device in LogicalDiscovery(scheduler, "BMC"):
	ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name_bmc", "emc_bmc_main.bin", "string"),Param("image_name_bb", "emc_bmc_BBLOCK.bin", "string"),Param("image_name_ssp", "emc_ssp_megatron.bin", "string"))
	ExecuteTest(scheduler, "update_firmware", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_bmc_main.bin", "string"), Param("image_id", "0x140", "hex"))
EndConcurrentTest(scheduler)

BeginConcurrentTest(scheduler)
for device in LogicalDiscovery(scheduler, "BMC"):
	ExecuteTest(scheduler, "update_firmware", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_bmc_BBLOCK.bin", "string"), Param("image_id", "0x144", "hex"))
EndConcurrentTest(scheduler)
BeginConcurrentTest(scheduler)
for device in LogicalDiscovery(scheduler, "BMC"):
	ExecuteTest(scheduler, "update_firmware", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_ssp_megatron.bin", "string"), Param("image_id", "0x142", "hex"))
EndConcurrentTest(scheduler)

Check_Device(nSP,LogicalDiscovery,scheduler, "LAN_Port0")
BeginConcurrentTest(scheduler)
for device in LogicalDiscovery(scheduler, "LAN_Port0"):
	ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_eth-fw_megatron_broadcom.bin", "string"))
	ExecuteTest(scheduler, "update_firmware", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_eth-fw_megatron_broadcom.bin", "string"))
EndConcurrentTest(scheduler)

Check_Device(nSP*4,GetGUIDByType,scheduler, "Local_Octane_Acbel_PS_Controller", "all")
BeginConcurrentTest(scheduler)
for device in GetGUIDByType(scheduler, "Local_Octane_Acbel_PS_Controller","local"):
	ExecuteTest(scheduler, "check_version", device, 
		Param("image_path", "/platypus/firmware", "string"), 
		Param("image_name", "emc_ps_octane_0802.bin", "string"))
	ExecuteTest(scheduler, "update_firmware", device, 
		Param("image_path", "/platypus/firmware", "string"), 
		Param("image_name", "emc_ps_octane_0802.bin", "string"), 
		Param("force", "yes", "string"))
EndConcurrentTest(scheduler)

Check_Device(nSP,LogicalDiscovery,scheduler, "SP_CMD")
BeginConcurrentTest(scheduler)
for device in LogicalDiscovery(scheduler, "SP_CMD"):
	ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("application_image", "emc_cmd-app_100d815pin.bin", "string"),  \
				Param("boot_block_image", "emc_cmd-bb_100d815pin.bin", "string"),Param("config_table_image", "emc_cmd-cfg_100d815pin.bin", "string"))
	ExecuteTest(scheduler, "update_firmware", device, Param("image_path", "/platypus/firmware", "string"), Param("application_image", "emc_cmd-app_100d815pin.bin", "string"),  \
				Param("boot_block_image", "emc_cmd-bb_100d815pin.bin", "string"),Param("config_table_image", "emc_cmd-cfg_100d815pin.bin", "string"))
EndConcurrentTest(scheduler)

Check_Device(nSP,LogicalDiscovery,scheduler, "CMI_0")
Check_Device(nSP,LogicalDiscovery,scheduler, "CMI_1")
Check_Device(nSP,LogicalDiscovery,scheduler, "CMI_2")
Check_Device(nSP,LogicalDiscovery,scheduler, "CMI_3")
BeginConcurrentTest(scheduler)
for device in LogicalDiscovery(scheduler, "CMI_0"):
	ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_pci-switch0_megatronB_plx.bin", "string"))
	ExecuteTest(scheduler, "update_firmware", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_pci-switch0_megatronB_plx.bin", "string"))
for device in LogicalDiscovery(scheduler, "CMI_1"):
	ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_pci-switch1_megatronB_plx.bin", "string"))
	ExecuteTest(scheduler, "update_firmware", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_pci-switch1_megatronB_plx.bin", "string"))
for device in LogicalDiscovery(scheduler, "CMI_2"):
	ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_pci-switch2_megatronB_plx.bin", "string"))
	ExecuteTest(scheduler, "update_firmware", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_pci-switch2_megatronB_plx.bin", "string"))
for device in LogicalDiscovery(scheduler, "CMI_3"):
	ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_pci-switch3_megatronB_plx.bin", "string"))
	ExecuteTest(scheduler, "update_firmware", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_pci-switch3_megatronB_plx.bin", "string"))
EndConcurrentTest(scheduler)

Check_Device(nSP,LogicalDiscovery,scheduler, "UEFI Firmware")
BeginConcurrentTest(scheduler)
for device in LogicalDiscovery(scheduler, "UEFI Firmware"):
	ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_uefi_fw_volume.bin", "string"))
	ExecuteTest(scheduler, "update_firmware", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_uefi_fw_volume.bin", "string"))
EndConcurrentTest(scheduler)

Check_Device(nSP*2,LogicalDiscovery,scheduler, "Mgmt_CMD")
BeginConcurrentTest(scheduler)
for device in GetGUIDByName(scheduler, "Mgmt_CMD","all"):
	Parents = QueryParentGUIDByGUID(scheduler,device)
	name = QueryNameByGUID(scheduler, Parents)
	if name.find("Local_ManagementModule")>-1:
		if name.find("Akula")>-1:
			ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("application_image", "emc_cmd-app_44pin.bin", "string"),  \
					Param("boot_block_image", "emc_cmd-bb_44pin.bin", "string"),Param("config_table_image", "emc_cmd-cfg_44pin.bin", "string"))
			ExecuteTestWithTimeout(scheduler, "update_firmware", device, 1800, Param("image_path", "/platypus/firmware", "string"), Param("application_image", "emc_cmd-app_44pin.bin", "string"),  \
					Param("boot_block_image", "emc_cmd-bb_44pin.bin", "string"),Param("config_table_image", "emc_cmd-cfg_44pin.bin", "string"))
EndConcurrentTest(scheduler)

Check_Device(nSP*2,LogicalDiscovery,scheduler, "Mgmt_MCU")
BeginConcurrentTest(scheduler)
for device in GetGUIDByName(scheduler, "Mgmt_MCU","all"):
	Parents = QueryParentGUIDByGUID(scheduler,device)
	name = QueryNameByGUID(scheduler, Parents)
	if name.find("Local_ManagementModule")>-1:
		if name.find("Akula")>-1:
			ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_mgmt_mcu_akula.bin", "string"))
			ExecuteTestWithTimeout(scheduler, "update_firmware", device, 1800, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_mgmt_mcu_akula.bin", "string"))
		if name.find("Management Module Control Station")>-1:
			ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_mgmt_mcu_mmcs.bin", "string"))
			ExecuteTestWithTimeout(scheduler, "update_firmware", device, 1800, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "emc_mgmt_mcu_mmcs.bin", "string"))
EndConcurrentTest(scheduler)

BeginConcurrentTest(scheduler)
for device in GetGUIDByNameRE(scheduler, "FIXED","all"):
		ExecuteTestWithTimeout(scheduler, "update_firmware", device, 1800,
							   Param("image_path", "/platypus/firmware", "string"),
							   Param("image_name", "emc_serdes_Megatron.bin", "string"))
EndConcurrentTest(scheduler)

BeginConcurrentTest(scheduler)
for device in GetGUIDByName(scheduler, "Moonlite_SAS_Controller", "all"):
	ExecuteTest(scheduler, "check_version", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name","spve_0208.bin", "string"))
	ExecuteTest(scheduler, "update_firmware", device, Param("image_path", "/platypus/firmware", "string"), Param("image_name", "spve_0208.bin", "string"), Param("force", "true", "bool"))
EndConcurrentTest(scheduler)
