import sys
import time
from System import Environment
from System import Random
from struct import pack
sys.path.append( Environment.CurrentDirectory )
from Platypus_Drive_API import *

test_config_dict = {"pattern_name": "none",
                    "duration": "00:00:00",
                    "segment_count_min": "1",
                    "segment_count_max": "1000",
                    "segment_size_in_blocks_min": "1",
                    "slice_count": "8",
                    "pattern_change_period": "00:00:00",
					"chunk_count":"1",
                    "chunk_number":"0",
                    "number_of_writes": 30000,
                    "number_of_ati_zones": 16,
                    "tracks_per_ati_zone": 100,
                    "lbas_per_track_filename": "LBASPERTRACK.txt"}

# Discover Backend Must ALWAYS be true unless otherwise debugging
discover_backend = True

#Check to make sure we have the correct platypus version
nondrive = NonDrive(scheduler)
nondrive.platypus_check(scheduler)
nondrive.echidna_check(scheduler)
sp_position = nondrive.sp_position(scheduler)

#Upload error_manager.xml Rulebook
FileTransfer(scheduler, "C:\\RDT\\Scripts\\error_manager.xml", "/platypus/policy/backend/", "local", {"Protocol":"FTP","Mode":"LAN"})

# Discover all drives in system
if discover_backend:
    BeginConcurrentTest(scheduler)
    for device in GetGUIDByType(scheduler, "System_Backend", "local"):
        ExecuteTest(scheduler, "backend_discovery_test", device, Param("force_rebuilding", "true", "bool"))# Gather drive information
	EndConcurrentTest(scheduler)

drives = Drives(scheduler,test_config_dict)

################################################################################
#################################### ATI #######################################
################################################################################    

#
# Build a dictionary of product ids to track sizes by parsing definition file
#
lbas_per_track = {}
try:
    with open(test_config_dict["lbas_per_track_filename"]) as f_in:
        for line in f_in:
            lbas_per_track[ line.split('/')[0] ] = int( line.split('/')[1] )
except:
    # Report error to user and stop the script.  The file must exist.
    VirtualTest(scheduler, 'open track definition file', True,
            '',
            'Error opening the track definition file: ' + test_config_dict["lbas_per_track_filename"])
    sys.exit("File Not Found. Stopping Script.")

    
#
# Create dictionary of unique product ids to track size and lba_max 
#
unique_product_ids = {}
ati_file_name = {}
for drive in drives.drive_list_single_path:
    # build list of tuples; product_id, lbas_per_track,lba_max
    prodid = drives.drive_info_dict[drive].info_items["product_identification"].rstrip()
    lba_max = long(drives.drive_info_dict[drive].info_items["returned_logical_block_address"], 16)
    if prodid not in unique_product_ids.keys():
        try:
            unique_product_ids[prodid] = (lbas_per_track[prodid], lba_max )
        except:
            # Report error to user and stop the script.  The drive must be defined
            # in the track definition file.
            VirtualTest(scheduler, 'track definition file search', True,
                    '',
                    'Product ID not found in track definition file: ' + prodid)
            sys.exit("Drive Product ID Not Found. Stopping Script.")
    ati_file_name[drive] = prodid+'_seek_'+sp_position+'.bin'
            
# create ati_zone and command files
for prodid in unique_product_ids:
    track_size, lba_max = unique_product_ids[prodid]
    ati_zone_starting_lbas = []
    for z in range(test_config_dict["number_of_ati_zones"]):
        ati_zone_starting_lbas.append( z*(lba_max+1)/test_config_dict["number_of_ati_zones"] )
    with open(prodid+'_seek_'+sp_position+'.bin','wb') as f_bin_out:
        with open(prodid+'_seek_'+sp_position+'.csv','w') as f_csv_out:
            for track_lba in range( track_size, track_size * test_config_dict["tracks_per_ati_zone"], track_size * 2 ):
                for zone_start_lba in ati_zone_starting_lbas:
                    lba = zone_start_lba + track_lba
                    data_out_bin = bytearray(12)
                    data_out_bin[0:7] = [ ord(b) for b in pack('<Q', lba )[0:7] ]
                    data_out_bin[8:11] = [ ord(b) for b in pack('<L', track_size )[0:3] ]
                    f_bin_out.write(data_out_bin)
                    f_csv_out.write(str(lba) + ',' + str(track_size) + '\n')

    # transfer to SP
    FileTransfer(scheduler, './'+prodid+'_seek_'+sp_position+'.bin', '/platypus', 'local', {'Protocol':'FTP','Mode':'AUTO'})

#Dump the drive logs
drives.get_logs()

for loop in range(4): #this loops ATI 4 times - 120,000 writes total   
#
# run the directed write then immediately followed by a read.  Let Platypus queue these
# two tests so we get the immediate read.  The timeout for the sequential read needs to
# account for the file_directed_test time.
#
    
    BeginConcurrentTest(scheduler)
    for drive in drives.drive_list_single_path:
		ExecuteTestWithTimeout(scheduler, 'file_directed_test', drive, 1209600,
            Param('pattern_custom', 'B1', 'string'),
            Param('write', 'true', 'bool'),
            Param('file_name', ati_file_name[drive],'string' ),
            Param('file_path', '/platypus', 'string'),
            Param('loop_count', str(test_config_dict["number_of_writes"]), 'dec') )
		ExecuteTestWithTimeout(scheduler, 'sequential_read', drive, 1209600,
            Param('pattern_custom','B1','string'))
    EndConcurrentTest(scheduler)
	
    #dump the drive logs
    drives.get_logs()

