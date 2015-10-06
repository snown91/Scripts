from PlatypusScripting import *
import re
import sys
import time
import os
import binascii
import csv
from struct import pack

class NonDrive:
    '''
    This API requires Platypus 10.12.0.2015-01-05_06-38-40 and Echidna 3.1.0.125!
    '''
    
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.CDI = GetGUIDByType(self.scheduler, "Root", "local")[0]
        self.echidna_version = Version(self.scheduler)
    
    def platypus_check(self, scheduler):
        required_platypus_version = "10.12.0.2015-01-05_06-38-40" #change requited platypus verison here
        results = ExecuteTestWithTimeout(self.scheduler, "identify", self.CDI, 60)
        platypus_version = ExtractData(results, "//version")
        
        if platypus_version == required_platypus_version:
            print "Platypus " + platypus_version + " is present! This is the correct version!"
        else:
            print "This script requires Platypus version " + required_platypus_version + "! You have Platypus version " + platypus_version + "!"
            sys.exit("See Script Output Tab for Error Information")
 
    def echidna_check(self, scheduler):
        required_echidna_version = "3.1.0.125"
        
        if self.echidna_version == required_echidna_version:
            print "Echidna " + self.echidna_version + " is present! This is the correct version!"
        else:
            print "This script required Echidna version " + required_echidna_version + "! You have Echidna version " + self.echidna_version + "!"
            sys.exit("See Script Output Tab for Error Information")
            
    def sp_position(self, scheduler):
    
        self.sp = GetGUIDByType(self.scheduler, "SP", "local")[0]
        
        BeginConcurrentTest(self.scheduler)
        results = ExecuteTestWithTimeout(self.scheduler, "identify", self.sp, 60)
        EndConcurrentTest(self.scheduler)
        
        sp_pos_string = ExtractData(results, "/data/device_info/position/dynamic")
        
        return sp_pos_string
        
            
# class that contains and stores information specific to a drive
class Drive_Info:
    # Query the drive for information.  Just store the result for now.  We will parse
    # the data in another step.  Split into two steps so this function can be called for
    # all drives at the same time.
    def __init__(self, scheduler, drive):
        self.scheduler = scheduler
        self.drive = drive
        self.report_characteristics = ExecuteTestWithTimeout(self.scheduler, "report_characteristics", drive, 600)
        self.indentify = ExecuteTestWithTimeout(self.scheduler, "identify", drive, 600)

    # Extract the interesting information from the data returned by the drive.  Put the information
    # into a dictionary for easy reference.
    def parse_information(self):
        self.info_items = {}

        self.info_items["t10_vendor_identification"] = ExtractData( self.report_characteristics, "/data/characteristic_data/t10_vendor_identification" ).strip()
        self.info_items["product_identification"] = ExtractData( self.report_characteristics, "/data/characteristic_data/product_identification" ).strip()
        self.info_items["product_revision_level"] = ExtractData( self.report_characteristics, "/data/characteristic_data/product_revision_level" ).strip()
        self.info_items["serial_number"] = ExtractData( self.report_characteristics, "/data/characteristic_data/serial_number" ).strip()
        self.info_items["tla"] = ExtractData( self.report_characteristics, "/data/characteristic_data/tla_part_number" ).strip()
        self.info_items["block_length_in_bytes"] = ExtractData( self.report_characteristics, "/data/characteristic_data/block_length_in_bytes" ).strip()
        self.info_items["returned_logical_block_address"] = ExtractData( self.report_characteristics, '//returned_logical_block_address').strip()
        self.info_items["protocol"] = ExtractData( self.report_characteristics, "/data/characteristic_data/protocol" ).strip()
        if self.info_items["protocol"] == "":
            self.info_items["protocol"] = "SAS"

        self.info_items["position_string"] = ExtractData( self.indentify, "/data/device_info/position/dynamic" )
        self.info_items["SLIC"] = ExtractData( self.indentify, "/data/device_info/position/descriptive/SLIC" )
        self.info_items["eses_dae"] = ExtractData( self.indentify, "/data/device_info/position/descriptive/ESES_DAE" )
        self.info_items["port"] = ExtractData( self.indentify, "/data/device_info/position/descriptive/SAS_Port" )
        self.info_items["controller"] = ExtractData( self.indentify, "/data/device_info/position/descriptive/SAS_Controller" )
        if self.info_items["port"] == None:
            self.info_items["port"] = ExtractData( self.indentify, "/data/device_info/position/descriptive/FC_Port" )
        self.info_items["slot"] = ExtractData( self.indentify, "/data/device_info/position/descriptive/Drive" )

    # Common function for reporting information about a drive
    def get_drive_info_str(self):
        drive_info_str = ""
        for info_item in self.info_items.keys():
            drive_info_str += info_item + ": " + self.info_items[info_item] + "\n"
        return drive_info_str

    # General function to run a drive test with a list of arguments.  The result is saved
    # for later use instead of returned so we can execute the test on a list of drives
    # simultaneously.
    def run_test(self,test_name,**arguments):
        # build a list of all the parameters
        arg_list = []
        for arg in arguments.keys():
            value, type = arguments[arg]
            p = Param(arg,value,type)
            arg_list.append(p)
        self.last_test_results = ExecuteTest(self.scheduler, test_name, self.drive, *arg_list )

    # Check that the drive currently reports the expected firmware revision
    def firmware_revision_check(self,expected_firmware_revision_level):
        at = ConstructAtomicTest("report_characteristics", self.drive)
        expected_result = ExpectedResultList(ExpectedResult("characteristic_data/product_revision_level",
                                                            0,
                                                            expected_firmware_revision_level,
                                                            "=") )
        ExecuteNormalTest(self.scheduler, at, expected_result )

    def phy_error_counter_check(self,maximum_count):
        at = ConstructAtomicTest("phy_error_counter_get", self.drive)
        expected_result = ExpectedResultList(ExpectedResult("log_sense_data/parameter/sas_phy_log_descriptor/invalid_dword_count",
                                                            0,
                                                            "%d" % maximum_count,
                                                            "<=") )
        self.last_test_results = ExecuteNormalTest(self.scheduler, at, expected_result )

    # Check that the drive reports the expected capacity
    def capacity_check(self,expected_capacity,expected_block_size):
        at = ConstructAtomicTest("read_capacity", self.drive)
        expected_result = ExpectedResultList(ExpectedResult("read_capacity_data/logical_block_address",
                                                            0,
                                                            "%x" % (expected_capacity-1),
                                                            "="),
                                             ExpectedResult("read_capacity_data/block_size",
                                                            0,
                                                            "%x" % expected_block_size,
                                                            "=") )
        self.last_test_results = ExecuteNormalTest(self.scheduler, at, expected_result )

    # Check that the defect count is under the specified limit
    def glist_check(self,glist_limit):
        at = ConstructAtomicTest("report_defect_counts", self.drive)
        expected_result = ExpectedResultList(ExpectedResult("defect_data/G_List_length",
                                                            0,
                                                            "%d" % glist_limit,
                                                            "<=") )
        self.last_test_results = ExecuteNormalTest(self.scheduler, at, expected_result )

    # check that the erase count is under the specified limit
    def erase_count_check(self,erase_count_limit):
        at = ConstructAtomicTest("report_erase_count", self.drive)
        expected_result = ExpectedResultList(ExpectedResult("log_sense_data/erase_count_statistics/maximum_erase_operations_on_any_flash_block_on_any_channel/count",
                                                            0,
                                                            "%d" % erase_count_limit,
                                                            "<=") )
        self.last_test_results = ExecuteNormalTest(self.scheduler, at, expected_result )

    # Grab the mode pages from the drive.
    def read_mode_pages(self,pc):
        self.drive_mode_pages_b64 = ExecuteTest(self.scheduler, "scsi_mode_sense_10", self.drive,
                                                Param("pc", pc, "hex"),
                                                Param("page_code", "3F","hex"),
                                                Param("allocation_length", "1000","hex"))
        self.last_test_results = self.drive_mode_pages_b64

    # Parse the binary mode page data from the drive into a 999 document like string and put into
    # a dictionary of mode pages using the page code as the key.  We currently do not list subpages
    # in the 999 document so no need for support here.
    def parse_mode_pages(self):
        mode_data = Convert.FromBase64String(ExtractData( self.drive_mode_pages_b64, "/data/data_in" ))

        # We are not interested in the header
        mode_data_list = list(mode_data)
        del mode_data_list[:16]

        # parse the mode data into the 999 document format
        page_str = "";
        page_length = 0
        self.mode_pages = {}
        for c in mode_data_list:
            # new page
            if page_str == "":
                page_code = c & 0x7F
                page_str = "%0.2X" % c
                continue

            # Add byte to our 999 document like string
            page_str += "-%0.2X" % c

            # This is the page length byte.
            if page_length == 0:
                page_length = c
                continue

            # If we are finished with this page, add to container
            page_length = page_length - 1
            if page_length == 0:
                self.mode_pages[page_code] = page_str
                page_str = "";


    # Modify the mode page dictionary according to the mode page specification defined in the
    # 999 document. 'X' is a don't core so leave those nibbles unchanged.
    def update_mode_page_data(self,pages_spec):
        # container of page_code,page_str tuples we will write back to the drive
        self.pages_select = []

        # iterate through each page of the spec and update with data from the drive.
        for page_code, page_str in pages_spec.items():
            # Did the drive report the page?
            if page_code not in self.mode_pages:
                output_str = "Error: Page %0.2X not reported by drive." % page_code + "\n"
                output_str += self.get_drive_info_str()
                print output_str
                continue

            # Was the page the correct length?
            if len(self.mode_pages[page_code]) != len(page_str):
                output_str = "Error: Length mismatch.\n"
                output_str += "Page %0.2X: " % page_code + page_str + "\n"
                output_str += "        " + self.mode_pages[page_code] + "\n"
                output_str += self.get_drive_info_str()
                print output_str
                continue

            # Update each nibble ignoring the don't cares and the '-' or ' ' delimiters
            mode_select_page_str = ""
            n = 0
            for nibble_drive in self.mode_pages[page_code]:
                nibble_spec = page_str[n]
                n += 1
                if nibble_spec == " " or nibble_spec == "-" or nibble_spec == "X":
                    mode_select_page_str += nibble_drive     # no change
                else:
                    mode_select_page_str += nibble_spec

            # Add to our data we will send to the drive with a mode select
            self.pages_select.append( (page_code,mode_select_page_str) )

    # Issue a mode select to the drive with the mode page information
    def write_mode_pages(self):
        mode_data = [0,0,0,0,0,0,0,0]   # header

        for page_code,page_str in self.pages_select:

            page_str.replace(" ","-")
            page_bytes = page_str.split("-")
            # The PS bit is reserved in mode select so clear it
            mode_data.append( int(page_bytes.pop(0), 16) & 0x7F )
            for b in page_bytes:
                mode_data.append( int(b, 16) )

        data_out = Convert.ToBase64String(Array[Byte] (mode_data))
        self.last_test_results = ExecuteTest(self.scheduler, "scsi_mode_select_10", self.drive,
                        Param("sp","true","bool"),
                        Param("parameter_list_length", "%0.4X"% len(mode_data),"hex"),
                        Param("data_out",data_out,"base64"))

# container that holds all drives and operates on a list of drives
class Drives:
    # Build a dictionary of drives and gather infromation about each one.  This function
    # will also clear any pending power on check conditions in case the drives were just
    # powered up.
    def __init__(self,scheduler,test_config_dict):
        # collect the data from the drives
        self.scheduler = scheduler
        self.test_config_dict = test_config_dict
        self.drive_list_all_paths = self.find_all_drives_all_paths()
        self.drive_info_dict = {}
        BeginConcurrentTest(self.scheduler)
        for drive in self.drive_list_all_paths:
            ExecuteTestWithTimeout(scheduler, "wait_unit_ready", drive, 600,
                        Param("do_not_report_filter","06/[0-9A-Fa-f]{2}/[0-9A-Fa-f]{2}","string"),
                        Param("duration","00:01:00","duration") )
        EndConcurrentTest(self.scheduler)
        
        BeginConcurrentTest(self.scheduler)
        for drive in self.drive_list_all_paths:
            self.drive_info_dict[drive] = Drive_Info(scheduler,drive)
        EndConcurrentTest(self.scheduler)


        # parse the data
        for drive in self.drive_info_dict.keys():
            self.drive_info_dict[drive].parse_information()
        
        self.drive_list_single_path = self.get_drive_list_single_path()
        
        if test_config_dict:
            self.drive_config_dict = self.configure_tests()

    # Setup the test configuration for each drive
    def initialize(self,drive_list):
        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            self.drive_info_dict[drive].initialize_test_configuration()
        self.scheduler.WaitForTestCompletion()
    
    # Determine the system configuration and return a list of drives split up by slic slot
    def get_drive_list_single_path(self):
        drive_list_single_path = []
        slic_list = []
        port_list = []
        controller_list = []
        dae_sets = []
        dae_list_all_paths = LocalLogicalDiscoveryByType(self.scheduler, "ESES_DAE") + LocalLogicalDiscoveryByType(self.scheduler, "Slave_ESES")# build a list of all DAE guids (this will include multiple paths to DAEs)
        for dae in dae_list_all_paths:
            temp_list = [dae]
            dae_drive_sn_set = set(self.get_serial_number_list(self.find_drives_by_dae_guid(dae)))
            for next_dae in dae_list_all_paths:
                next_dae_drive_sn_set = set(self.get_serial_number_list(self.find_drives_by_dae_guid(next_dae)))
                if dae_drive_sn_set == next_dae_drive_sn_set:
                    temp_list.append(next_dae)
            if set(temp_list) not in dae_sets:
                dae_sets.append(set(temp_list))
        for drive in self.drive_list_all_paths:
            if int(self.drive_info_dict[drive].info_items["SLIC"]) not in slic_list:
                slic_list.append(int(self.drive_info_dict[drive].info_items["SLIC"])) # build a list of all slics in use
            if int(self.drive_info_dict[drive].info_items["controller"]) not in controller_list:
                controller_list.append(int(self.drive_info_dict[drive].info_items["controller"])) # build a list of all controllers in use
            if int(self.drive_info_dict[drive].info_items["port"]) not in port_list:
                port_list.append(int(self.drive_info_dict[drive].info_items["port"])) # build a list of all ports in use
        for dae_set in dae_sets:
            paths = len(dae_set)
            modulo = 0
            for dae in dae_set:
                drive_list_dae = self.find_drives_by_dae_guid(dae) # list of all drives connected to this dae
                for slic in slic_list:
                    drive_list_slic = self.find_drives_by_slic_list([slic]) # list of all drives connected to this slic
                    for controller in controller_list:
                        drive_list_controller = self.find_drives_by_controller_list([controller]) # list of all drives connected to this controller
                        for port in port_list:
                            drive_list_modulo = self.find_drives_by_slot_modulo(paths,modulo) # divide the drives up amongst each path
                            drive_list_port = self.find_drives_by_port_list([port]) # list of all drives connected to this port
                            drive_list_path = list( set(drive_list_modulo) # list of drives that are in this DAE & SLIC & controller & port
                                                    & set(drive_list_dae)
                                                    & set(drive_list_slic)
                                                    & set(drive_list_controller)
                                                    & set(drive_list_port))
                            if len(drive_list_path) > 0:
                                modulo += 1  # if there's at least one drive that matches the criteria, increment the slot modulo and append the list
                                drive_list_single_path += drive_list_path
        return drive_list_single_path

    # GUIDs of all drive logical devices
    def find_all_drives_all_paths(self):
        return LocalLogicalDiscoveryByType(self.scheduler, "Drive")
    
    def find_drives_by_dae_guid(self, dae_guid):
        drive_list = GetIntersection(QueryChildrenGUIDByGUID(self.scheduler, dae_guid), self.drive_list_all_paths)
        return drive_list

    # GUIDs of drive logical devices remove duplicate paths
    def find_all_physical_drives(self):
        drives = []
        sn = []
        for drive in self.drive_info_dict.keys():
            drive_info = self.drive_info_dict[drive]
            drive_serial_number = drive_info.info_items["serial_number"]
            if drive_serial_number not in sn:
                sn.append( drive_serial_number )
                drives.append( drive )
        return drives
    
    def get_serial_number_list(self, drive_list):
        serial_number_list = []
        for drive in drive_list:
            serial_number_list.append(self.drive_info_dict[drive].info_items["serial_number"])
        return serial_number_list

    # look for specific product IDs
    def find_drives_by_product_identification( self, product_id ):
        drives = []
        for drive in self.drive_info_dict.keys():
            # get drive information
            drive_info = self.drive_info_dict[drive]
            # All one drive type
            if None != re.search(product_id,drive_info.info_items["product_identification"]):
                drives.append(drive)
        return drives

    # look for drives by slot based on modulo
    def find_drives_by_slot_modulo( self, slot_divisor, slot_modulo ):
        drives = []
        for drive in self.drive_info_dict.keys():
            # get drive information
            drive_info = self.drive_info_dict[drive]
            # Example selecting by position
            if int(drive_info.info_items["slot"]) % slot_divisor == slot_modulo:
                drives.append(drive)
        return drives

    # look for drives by slot based on list of slots
    def find_drives_by_slot_list( self, slots ):
        drives = []
        for drive in self.drive_info_dict.keys():
            # get drive information
            drive_info = self.drive_info_dict[drive]
            # Example selecting by position
            if int(drive_info.info_items["slot"]) in slots:
                drives.append(drive)
        return drives

    # look for drives by SLIC based on list of SLICs
    def find_drives_by_slic_list( self, slics ):
        drives = []
        for drive in self.drive_info_dict.keys():
            # get drive information
            drive_info = self.drive_info_dict[drive]
            if "" != drive_info.info_items["SLIC"]:
                if int(drive_info.info_items["SLIC"]) in slics:
                    drives.append(drive)
        return drives

    # look for drives by port based on list of ports
    def find_drives_by_port_list( self, ports ):
        drives = []
        for drive in self.drive_info_dict.keys():
            # get drive information
            drive_info = self.drive_info_dict[drive]
            # Example selecting by position
            if int(drive_info.info_items["port"]) in ports:
                drives.append(drive)
        return drives
    
    # look for drives by controller based on list of controllers
    def find_drives_by_controller_list( self, controllers ):
        drives = []
        for drive in self.drive_info_dict.keys():
            # get drive information
            drive_info = self.drive_info_dict[drive]
            # Example selecting by position
            if int(drive_info.info_items["controller"]) in controllers:
                drives.append(drive)
        return drives

    # look for drives by DAE based on list of DAEs
    def find_drives_by_dae_list( self, daes ):
        drives = []
        for drive in self.drive_info_dict.keys():
            # get drive information
            drive_info = self.drive_info_dict[drive]
            # Example selecting by position
            if int(drive_info.info_items["eses_dae"]) in daes:
                drives.append(drive)
        return drives

    # build a string that describes all the drives in the given list
    def get_drive_descriptions(self,drive_list):
        drive_info_str = ""
        for drive in drive_list:
            drive_info_str += self.drive_info_dict[drive].get_drive_info_str() + "\n"
        return drive_info_str

    # Cleanup from previous tests
    def drive_test_cleanup(self,drive_list):
        self.scheduler.IsQueueTests = 0
        # turn all the LEDs off
        for drive in drive_list:
            self.drive_info_dict[drive].run_test("fault_led_off")
        # restore all the defaults
        for drive in drive_list:
            self.drive_info_dict[drive].run_test("configure", restore_defaults=("true","bool") )
        self.scheduler.WaitForTestCompletion()

    # Run a test on all the drives in the list
    def run_test(self,drive_list,test_name,**arguments):
        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            self.drive_info_dict[drive].run_test(test_name,**arguments)
        self.scheduler.WaitForTestCompletion()

    # Run a test on all the drives in the list
    def start_test(self,drive_list,test_name,**arguments):
        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            self.drive_info_dict[drive].run_test(test_name,**arguments)

    # power on the drive slot and be sure we get the proper check condition
    def power_cycle(self,drive_list,off_time_in_ms):
        # drives off
        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            self.drive_info_dict[drive].run_test("power_off")
        self.scheduler.WaitForTestCompletion()

        # delay
        time.sleep( off_time_in_ms )

        # drives on
        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            self.drive_info_dict[drive].run_test("power_on")
        self.scheduler.WaitForTestCompletion()

        # delay.  All drives should be ready in 60 seconds or less otherwise fail
        time.sleep( 60 )

        # All drive paths should post a check condition
        all_paths_to_drives_in_list = []
        for target_drive in drive_list:
            target_drive_serial_number = self.drive_info_dict[target_drive].info_items["serial_number"]
            for drive in self.drive_info_dict.keys():
                if target_drive_serial_number == self.drive_info_dict[drive].info_items["serial_number"]:
                    all_paths_to_drives_in_list.append( drive )

        self.scheduler.IsQueueTests = 0
        for drive in all_paths_to_drives_in_list:
            wur = ConstructAtomicTest("wait_unit_ready", drive, Param("duration","00:01:00","duration"))
            expected_error_codes = ErrorCodeList(ErrorCode('1000000002162901', 'Unit Attention') )
            ExecuteNegativeTest(self.scheduler, wur, expected_error_codes )
        self.scheduler.WaitForTestCompletion()

    # Check the firmware revisions
    def firmware_revision_check(self,drive_list):
        for drive in drive_list:
            drive_info = self.drive_info_dict[drive]
            if drive_info.info_items["tla"] in tla_to_999_info_dict:
                fw_in_999 = tla_to_999_info_dict[drive_info.info_items["tla"]].info["firmware"]
                drive_info.firmware_revision_check(fw_in_999)
            else:
                error_str = "Error: firmware revision test : TLA not found in dictionary: "
                error_str += drive_info.info_items["tla"] + "\n"
                error_str += drive_info.get_drive_info_str()
                print error_str

    # Reset the phy error counters
    def phy_error_counter_reset(self,drive_list):
        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            self.drive_info_dict[drive].run_test("phy_error_counter_reset")
        self.scheduler.WaitForTestCompletion()

    # Check the phy error counters for change
    def phy_error_counter_check(self,drive_list):
        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            self.drive_info_dict[drive].phy_error_counter_check(0)
        self.scheduler.WaitForTestCompletion()

    # Check the format
    def format_check(self,drive_list):
        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            drive_info = self.drive_info_dict[drive]
            if drive_info.info_items["tla"] in tla_to_999_info_dict:
                capacity_in_999 = tla_to_999_info_dict[drive_info.info_items["tla"]].info["capacity"]
                block_size_in_999 = tla_to_999_info_dict[drive_info.info_items["tla"]].info["block_size"]
                drive_info.capacity_check(capacity_in_999, block_size_in_999)
            else:
                error_str = "Error: format check test : TLA not found in dictionary: "
                error_str += drive_info.info_items["tla"] + "\n"
                error_str += drive_info.get_drive_info_str()
                print error_str
        self.scheduler.WaitForTestCompletion()

    # Check the GLIST
    def glist_check(self,drive_list):
        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            drive_info = self.drive_info_dict[drive]
            if drive_info.info_items["tla"] in tla_to_999_info_dict:
                glist_limit = tla_to_999_info_dict[drive_info.info_items["tla"]].info["glist_limit"]
                drive_info.glist_check(glist_limit)
            else:
                error_str = "Error: GLIST check test : TLA not found in dictionary: "
                error_str += drive_info.info_items["tla"] + "\n"
                error_str += drive_info.get_drive_info_str()
                print error_str
        self.scheduler.WaitForTestCompletion()

    # Check the flash drive erase count
    def erase_count_check(self,drive_list):
        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            drive_info = self.drive_info_dict[drive]
            if drive_info.info_items["tla"] in tla_to_999_info_dict:
                erase_count_limit = tla_to_999_info_dict[drive_info.info_items["tla"]].info["erase_count_limit"]
                if erase_count_limit != None:
                    drive_info.erase_count_check(erase_count_limit)
            else:
                # Maybe not an SSD drive
                error_str = "Error: erase count check test : TLA not found in dictionary: "
                error_str += drive_info.info_items["tla"] + "\n"
                error_str += drive_info.get_drive_info_str()
                print error_str
        self.scheduler.WaitForTestCompletion()

    # Read the mode pages according to the 999 document
    def mode_sense(self,drive_list):
        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            drive_info = self.drive_info_dict[drive]
            drive_info.read_mode_pages()
        self.scheduler.WaitForTestCompletion()
        for drive in drive_list:
            drive_info = self.drive_info_dict[drive]
            drive_info.parse_mode_pages()

    # Read modify write the mode pages according to the 999 document
    def mode_select(self,drive_list):
        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            drive_info = self.drive_info_dict[drive]
            drive_info.read_mode_pages()
        self.scheduler.WaitForTestCompletion()

        for drive in drive_list:
            drive_info = self.drive_info_dict[drive]
            drive_info.parse_mode_pages()

        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            drive_info = self.drive_info_dict[drive]
            if drive_info.info_items["tla"] not in tla_to_999_info_dict:
                error_str = "Error: mode page update: TLA not found in dictionary: "
                error_str += drive_info.info_items["tla"] + "\n"
                error_str += drive_info.get_drive_info_str()
                print error_str
                continue

            doc = tla_to_999_info_dict[ drive_info.info_items["tla"] ].info["document_number"]
            if doc not in mode_page_spec_dict:
                error_str = "Error: mode page update: 999 doc not found in dictionary: "
                error_str += doc + "\n"
                error_str += drive_info.get_drive_info_str()
                print error_str
                continue

            pages_spec = mode_page_spec_dict[ doc ]
            drive_info.update_mode_page_data(pages_spec)

            drive_info.write_mode_pages()
        self.scheduler.WaitForTestCompletion()

    def emc_unique_data_collection_clear(self,drive_list):
        self.scheduler.IsQueueTests = 0
        for drive in drive_list:
            drive_info = self.drive_info_dict[drive]
            if drive_info.info_items["tla"] not in tla_to_999_info_dict:
                error_str = "Error: clearing EMC unique data collection: TLA not found in dictionary: "
                error_str += drive_info.info_items["tla"] + "\n"
                error_str += drive_info.get_drive_info_str()
                print error_str
                continue
            byte_6 = tla_to_999_info_dict[ drive_info.info_items["tla"] ].info["f7_cmd_byte_6"]
            drive_info.run_test("scsi_emc_unique_data_collection",
                                retrieve_dump = ("false","bool"),
                                trigger_dump = ("false","bool"),
                                clear_dump = ("true","bool"),
                                emc_unique_f7_cmd_byte_6_value = (byte_6,"hex"),
                                transfer_length = ("0","hex") )
        self.scheduler.WaitForTestCompletion()

    def performance_report(self,drive_list):
        test_duration = {}
        total_data_in = {}
        total_data_out = {}
        total_commands_sent = {}
        transfer_rate = {}
        iops = {}

        for drive in drive_list:
            drive_info = self.drive_info_dict[drive]

            td_str = ExtractData( drive_info.last_test_results, "/data/statistics/test_duration" )
            td_split = td_str.split(':')
            hours = float(td_split[0])
            minutes = float(td_split[1])
            seconds = float(td_split[2])
            test_duration[drive] = seconds + minutes * 60.0 + hours * 3600.0

            total_data_in[drive] = float(ExtractData( drive_info.last_test_results, "/data/statistics/total_data_in" ))
            total_data_out[drive] = float(ExtractData( drive_info.last_test_results, "/data/statistics/total_data_out" ))
            total_commands_sent[drive] = float(ExtractData( drive_info.last_test_results, "/data/statistics/total_commands_sent" ))

            iops[drive] = total_commands_sent[drive] / test_duration[drive]
            transfer_rate[drive] = (total_data_in[drive] + total_data_out[drive]) / 1000000.0 / test_duration[drive]

        test_transfer_rate = 0.00
        test_iops = 0.00
        for drive in drive_list:
            test_transfer_rate += transfer_rate[drive]
            test_iops += iops[drive]
        average_transfer_rate = test_transfer_rate / len(drive_list)

        output_str  = "Drives tested:         %d" % len(drive_list) + "\n"
        output_str += "Test transfer rate:    %.2f" % test_transfer_rate + " MB/s\n"
        output_str += "Test operations:       %.0f" % test_iops + " IOPS\n"
        output_str += "Highest transfer rate: %.2f" % max(transfer_rate.values()) + " MB/s\n"
        output_str += "Average transfer rate: %.2f" % average_transfer_rate + " MB/s\n"
        output_str += "Lowest transfer rate:  %.2f" % min(transfer_rate.values()) + " MB/s\n"
        return output_str

    def csv_log_header(self):
        csv_header = ",drive,test_duration,total_data_in,total_data_out,total_commands_sent"
        return csv_header

    def csv_log(self,drive_list):
        csv_str_list = []
        for drive in drive_list:
            csv_str = ","
            csv_str += drive
            drive_info = self.drive_info_dict[drive]

            td_str = ExtractData( drive_info.last_test_results, "/data/statistics/test_duration" )
            td_split = td_str.split(':')

            hours = float(td_split[0])
            minutes = float(td_split[1])
            seconds = float(td_split[2])
            test_duration = seconds + minutes * 60.0 + hours * 3600.0
            csv_str += ",%d"%test_duration

            csv_str += ","
            csv_str += ExtractData( drive_info.last_test_results, "/data/statistics/total_data_in" )
            csv_str += ","
            csv_str += ExtractData( drive_info.last_test_results, "/data/statistics/total_data_out" )
            csv_str += ","
            csv_str += ExtractData( drive_info.last_test_results, "/data/statistics/total_commands_sent" )
            csv_str_list.append(csv_str)

        return csv_str_list

    def get_mode_pages(self,drive,pc):
        drive_info = self.drive_info_dict[drive]
        drive_info.read_mode_pages(pc)
        drive_info.parse_mode_pages()
        return drive_info.mode_pages

    def change_mode_pages(self,drive,page_data):
        drive_info = self.drive_info_dict[drive]
        drive_info.update_mode_page_data(page_data)
        drive_info.write_mode_pages()
        
    def configure_tests(self):
        drive_config_dict = {}
        
        BeginConcurrentTest(self.scheduler)    
        for drive in self.drive_list_all_paths:
            drive_config_dict[drive] = {}
            
            #Make the string for the writesame test
            drive_config_dict[drive]["data_out_string"] = "0x" + self.drive_info_dict[drive].info_items["block_length_in_bytes"] + ":DE AD BE EF"
            
            #Calculate timeout
            if self.drive_info_dict[drive].info_items["protocol"] == "SAS":
                drive_config_dict[drive]["timeout"] = (int(self.drive_info_dict[drive].info_items["returned_logical_block_address"], 16) * int(self.drive_info_dict[drive].info_items["block_length_in_bytes"], 16)) / 25043040 #41943040
            if self.drive_info_dict[drive].info_items["protocol"] == "SATA":
                drive_config_dict[drive]["timeout"] = (int(self.drive_info_dict[drive].info_items["returned_logical_block_address"], 16) * int(self.drive_info_dict[drive].info_items["block_length_in_bytes"], 16)) / 6001175
            
            #Pick the seek type
            if self.drive_info_dict[drive].info_items["protocol"] == "SATA":
                drive_config_dict[drive]["seek_type"] = "read"
            else:
                drive_config_dict[drive]["seek_type"] = "seek"
            
            #Check the block size and set transfers accordingly
            if int(self.drive_info_dict[drive].info_items["block_length_in_bytes"],16) < 600:
                drive_config_dict[drive]["transfer_size"] = "1000"
                drive_config_dict[drive]["segment_size"] = "1000"
                drive_config_dict[drive]["verification_size"] = "1000"
            else:
                drive_config_dict[drive]["transfer_size"] = "200"
                drive_config_dict[drive]["segment_size"] = "200"
                drive_config_dict[drive]["verification_size"] = "200"
                
            for key in self.test_config_dict:
                drive_config_dict[drive][key] = self.test_config_dict[key]
                
            #Set the global drive parameters    
        
            ExecuteTestWithTimeout(self.scheduler, "configure", drive, 300,
                Param("pattern_name", self.test_config_dict["pattern_name"], "string"),
                Param("duration", self.test_config_dict["duration"],"duration"),
                Param("segment_count_min", self.test_config_dict["segment_count_min"], "dec"),
                Param("segment_count_max", self.test_config_dict["segment_count_max"], "dec"),
                Param("segment_size_in_blocks_min", self.test_config_dict["segment_size_in_blocks_min"], "hex"),
                Param("segment_size_in_blocks_max", drive_config_dict[drive]["segment_size"], "hex"),
                Param("transfer_size_in_blocks_min", drive_config_dict[drive]["transfer_size"], "hex"),
                Param("transfer_size_in_blocks_max", drive_config_dict[drive]["transfer_size"], "hex"),
                Param("slice_count", self.test_config_dict["slice_count"], "dec"),
                Param("pattern_change_period", self.test_config_dict["pattern_change_period"], "duration"))
            ExecuteTestWithTimeout(self.scheduler, "set_lba_range", drive, 300,
                Param("chunk_count", self.test_config_dict["chunk_count"], "dec"),
                Param("chunk_number", self.test_config_dict["chunk_number"], "dec"))
        EndConcurrentTest(self.scheduler)
            
        return drive_config_dict
    
    # Set each drive's saved values to the default values
    # Check these values against the 999 doc
    # Set AWRE and ARRE to 0 and verify the change
    def mode_page_check(self):
        date = time.strftime("%d_%m_%y")
        path = 'c:\\RDT\\MODEPAGES\\' + date + '\\'
        if not os.path.exists(path):
            os.makedirs(path)
        outfile = open(path + date + ".csv", 'wb')
        outfile_writer = csv.writer(outfile, dialect='excel')
        outfile_writer.writerow(["Position", "Serial #", "Spec Values", "Drive Values"])
        specfile = open('specfile.txt', 'r')
        spec_values = {}
        mismatch_dict = {}
        for line in specfile:
            page_code = int(line[0:2], 16) - 128
            spec_values[page_code] = line.rstrip()
        specfile.close()
        for drive in self.drive_list_single_path:
            if self.drive_info_dict[drive].info_items["protocol"] == "SAS":
                mismatch_dict[drive] = []
                default_values = self.get_mode_pages(drive,"2") #read in the default values
                self.change_mode_pages(drive, default_values) #change the saved values to the default values
                saved_values = self.get_mode_pages(drive,"3") #read in those new saved values
                new_page_1 = ''
                for byte, value in enumerate(saved_values[1]):
                    if byte == 6:
                        new_page_1 = new_page_1 + '0'
                    else:
                        new_page_1 = new_page_1 + value
                saved_values[1] = new_page_1
                self.change_mode_pages(drive, saved_values)
                saved_values = self.get_mode_pages(drive,"3") #read them back again to make sure
                for page_code, page_data in spec_values.items():
                    if page_code in saved_values: #make sure the drive supports the page code
                        if int(page_data[3:4], 16) > int(saved_values[page_code][3:4], 16):
                            print "Page " + str(page_code) + " length mismatch\n"
                            print "Expected " + page_data[3:4] + " got " + saved_values[page_code][3:4] + "\n"
                            print "Spec: " + page_data + "\n"
                            print "Drive: " + saved_values[page_code]
                            mismatch_dict[drive].append([self.drive_info_dict[drive].info_items["position_string"],
                                                        self.drive_info_dict[drive].info_items["serial_number"],
                                                        page_data,
                                                        saved_values[page_code]])
                            continue
                        for byte, value in enumerate(page_data):
                            if value != 'X' and value != '-' and value != saved_values[page_code][byte]: #make sure all the important bytes match the spec
                                print "Page " + str(page_code) + " mismatch\n"
                                print "Expected " + value + " got " + saved_values[page_code][byte] + "\n"
                                print "Spec: " + page_data + "\n"
                                print "Drive: " + saved_values[page_code]
                                mismatch_dict[drive].append([self.drive_info_dict[drive].info_items["position_string"],
                                                            self.drive_info_dict[drive].info_items["serial_number"],
                                                            page_data,
                                                            saved_values[page_code]])
                    else:
                        print "Page " + str(page_code) + " not supported by drive"
                        mismatch_dict[drive].append([self.drive_info_dict[drive].info_items["position_string"],
                                                    self.drive_info_dict[drive].info_items["serial_number"],
                                                    "Page " + str(page_code),
                                                    "Not Supported"])
                with open(path + self.drive_info_dict[drive].info_items["serial_number"] + ".txt", 'w') as printpages:
                    for page in saved_values:
                        printpages.write(saved_values[page] + "\n")
        for drive in mismatch_dict:
            if len(mismatch_dict[drive]) > 0:
                for mismatch in mismatch_dict[drive]:
                    outfile_writer.writerow(mismatch)
        outfile.close()
        return mismatch_dict

    def get_logs(self):
        page_list = ["02", "03", "05", "06", "0D", "0E", "15", "18", "1A"]
    
        # G-List Check #############################################################
        BeginConcurrentTest(self.scheduler)
        for drive in self.drive_list_single_path:
            ExecuteTestWithTimeout(self.scheduler, "report_defect_counts", drive, 300)
        EndConcurrentTest(self.scheduler)
        
        # SATA SMART Log Check ######################################################
        BeginConcurrentTest(self.scheduler)
        for drive in self.drive_list_single_path:
            if self.drive_info_dict[drive].info_items["protocol"] == "SATA":
                ExecuteTestWithTimeout(self.scheduler, "sata_smart", drive, 300,
                            Param("count", "1", "hex"),
                            Param("features", "D0", "hex"), #Feature 0D SATA READ DATA
                            Param("lba_low", "0", "hex"))
        EndConcurrentTest(self.scheduler)

        # Log Page Check ###########################################################
        for page in page_list:
            BeginConcurrentTest(self.scheduler)
            for drive in self.drive_list_single_path:
                if self.drive_info_dict[drive].info_items["protocol"] == "SAS":
                    ExecuteTestWithTimeout(self.scheduler, "scsi_log_sense", drive, 300,
                        Param("allocation_length", "FFFF", "hex"),
                        Param("page_code", page, "hex"),
                        Param("subpage_code", "0", "hex"),
                        Param("parameter_pointer", "0", "hex"),
                        Param("pc", "1", "hex"),
                        Param("sp", "false", "bool"))
            EndConcurrentTest(self.scheduler)
        
    def E6_SMART_Dump(self):
        # Smart Dump (E6) ##########################################################
        date = time.strftime("%d_%m_%y")
        path = 'c:\\RDT\\SMART\\' + date
        if not os.path.exists(path):
            os.makedirs(path)
                        
        for drive in self.drive_list_single_path:
            if self.drive_info_dict[drive].info_items["protocol"] == "SAS":
                drive_serial = self.drive_info_dict[drive].info_items["serial_number"].strip()
                offset_string = '0'    
                filename_bin = drive_serial + "_" + date +".bin"
                f = open('c:\\RDT\\SMART\\' + date + '\\' + filename_bin,"wb")
                while True:
                    results = ExecuteTestWithTimeout(self.scheduler, "scsi_smart_dump", drive, 300,
                                                    Param("allocation_length", "1048576", "dec"),
                                                    Param("offset", offset_string, "dec"))
                    offset_int = (int(offset_string) + 1048576)
                    offset_string = str(offset_int)
                    self.scheduler.WaitForTestCompletion()
                    if HasError(results):
                        f.flush()
                        f.close()
                        break 
                    else:
                        binresults = binascii.a2b_base64(GetTestOutput(results,"//data_in"))
                        f.write(binresults)
