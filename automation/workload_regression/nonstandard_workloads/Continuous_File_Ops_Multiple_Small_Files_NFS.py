# SMGLNSN
'''
###############################################################################################################
# Testcase Name : Continuous_File_Ops_Multiple_Small_Files_NFS                                                #
#                                                                                                             #
# Testcase Description : This test performs the following actions continuously for fixed set of iterations :  #
#                        a) Creates multiple small files of varying size (1-10MB) on the NFS volume,          #
#                        b) writes into the above files,                                                      #
#                        c) reads from the above files and                                                    # 
#                        d) Deletes them after a fixed period                                                 #
#                                                                                                             # 
# Testcase Pre-Requisites : Pool has to be created                                                            #
#                                                                                                             #
# Testcase Creation Date : 27/04/2016                                                                         #
#                                                                                                             #
# Testcase Last Modified : 27/04/2016                                                                         #  
#                                                                                                             #  
# Modifications made : None                                                                                   #  
#                                                                                                             #
# Testcase Author : Karthik,Mardan                                                                            #
###############################################################################################################
'''
# Import necessary packages and methods

import sys
import json
import logging
from time import ctime
from cbrequest import get_url, configFile, sendrequest, resultCollection, \
        get_apikey, mountNFS, executeCmd, sshToOtherClient, putFileToController, \
        sshToRemoteClient
from utils import check_mendatory_arguments, is_blocked, get_logger_footer
from haUtils import get_controller_info, list_controller, get_value, get_node_IP
from poolUtils import listPool, get_pool_info, getFreeDisk, getDiskToAllocate, \
        create_pool, listDiskGroup, delete_pool
from accountUtils import get_account_id
from tsmUtils import listTSMWithIP_new, create_tsm, delete_tsm
from volumeUtils import create_volume, delete_volume, addNFSclient, \
        listVolumeWithTSMId_new

'''
# Clear configuration before this test begins


CleanUpResult = CleanUp(STDURL)
if CleanUpResult[0] == 'FAILED':
    logging.error('Cleanup before starting testcase Continuous_File_Ops_Multiple_Small_Files_NFS')
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)
'''

# Clear the log file before execution starts

executeCmd('> logs/automation_execution.log')

# Initialization for Logging location 

logging.basicConfig(format = '%(asctime)s %(message)s', filename = \
        'logs/Continuous_File_Ops_Multiple_Small_Files_NFS.log', filemode = 'a', level = logging.DEBUG)

# Initialization for few common global variables

startTime = ctime()
HEADER_MSG = 'Testcase "Continuous_File_Ops_Multiple_Small_Files_NFS" is started'
FOOTER_MSG = 'Testcase "Continuous_File_Ops_Multiple_Small_Files_NFS" is completed'
BLOCKED_MSG = 'Testcase "Continuous_File_Ops_Multiple_Small_Files_NFS" is blocked'
EXECUTE_SYNATX = 'python Continuous_File_Ops_Multiple_Small_Files_NFS.py conf.txt'

logging.info('%s', HEADER_MSG)

# Check for correct usage of script

check_mendatory_arguments(sys.argv, 2, EXECUTE_SYNATX, FOOTER_MSG, BLOCKED_MSG, startTime)

# Get necessary params and values from config file (conf.txt)

conf = configFile(sys.argv)
DEVMAN_IP = conf['host']
USER = conf['username']
PASSWORD = conf['password']

APIKEY = get_apikey(conf)
APIKEY = APIKEY[1]
STDURL = get_url(conf, APIKEY)

POOL_TYPE = conf['pool_type']
NUM_POOL_DISKS = conf['num_pool_disks']
POOL_DISK_TYPE = conf['pool_disk_type']
POOL_IOPS = conf['pool_iops']
POOL_NAME = 'POOLTEST'

VSM_IP = conf['ipVSM1']
VSM_INTERFACE = conf['interfaceVSM1']
VSM_DNS = conf['dnsVSM1']
VSM_NAME = 'VSMTEST'

VOL_NAME = 'VolTest1'

CLIENT1_IP = conf['Client1_IP']
CLIENT1_USER = conf['Client1_user'] 
CLIENT1_PASSWORD = conf['Client1_pwd']

CLIENT_NFS_MOUNT_PNT = '/mnt/nfs_cont_file_ops_multiple_small'

logging.debug('DEVMAN_IP: %s', DEVMAN_IP)
logging.debug('USER: %s', USER)
logging.debug('PASSWORD: %s', PASSWORD)
logging.debug('VSM_IP: %s', VSM_IP)
logging.debug('APIKEY: %s', APIKEY)
logging.debug('STDURL: %s', STDURL)


# definitions for some methods used in this script

def verify_list_controller(list_cntrl, startTime):
    if list_cntrl[0] == 'PASSED':
        return list_cntrl[1]
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
            ': %s',list_cntrl[1])
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)

def verify_get_controller_info(get_info, startTime):
    if get_info[0] == 'PASSED':
        return
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
            ': %s', get_info[1])
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)

def verify_create_volume(result):
    if result[0] == 'PASSED':
        return
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
            ': %s', result[1])
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)

# Getting controller info and state before creating pool

startTime = ctime()
list_cntrl = list_controller(STDURL)
controllers = verify_list_controller(list_cntrl, startTime)
controllers_ip, num_of_Nodes = get_node_IP(controllers)
if num_of_Nodes == 1:
    NODE1_IP = controllers_ip[0]
elif num_of_Nodes == 2:
    NODE1_IP = controllers_ip[0]
    NODE2_IP = controllers_ip[1]
else:
    logging.debug('No support yet for clusters with greater than 2 nodes')
    exit()

get_info = get_controller_info(NODE1_IP, controllers)
verify_get_controller_info(get_info, startTime)
status, ctrl_name, ctrl_id, ctrl_ip, ctrl_cluster_id, ctrl_disks, \
        site_id = get_value(get_info)

if status.lower() == 'maintenance' and num_of_Nodes == 2:
    logging.debug('Node1 is in maintenance, checking status of Node2')
    get_info = get_controller_info(NODE2_IP, controllers)
    verify_get_controller_info(get_info, startTime)
    status, ctrl_name, ctrl_id, ctrl_ip, ctrl_cluster_id, ctrl_disks, \
            site_id = get_value(get_info)
    if status.lower() == 'maintenance':
        logging.error('Both nodes are in maintenance, testcase cannot proceed')
        is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)
elif status.lower() == 'maintenance' and num_of_Nodes == 1:
    logging.error('The single node in HAgroup is in maintenance, testcase cannot proceed')
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)
    
# Steps to get free disk list for pool creation

freedisk = getFreeDisk(ctrl_disks)
if freedisk[0] == 'FAILED':
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
           ': %s', freedisk[1])
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)
freedisk = freedisk[1]

# Steps to get allocatable disks for pool (based on size, type etc..,)

allocatable_diskidlist = getDiskToAllocate(freedisk, NUM_POOL_DISKS, POOL_DISK_TYPE)

if allocatable_diskidlist[0] == 'FAILED':
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
            ': %s', allocatable_diskidlist[1])
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)
allocatable_diskidlist = allocatable_diskidlist[1]

# Get params for pool creation (Needs controller, pool info etc..,)

pool_params = {'name': POOL_NAME, 'siteid': site_id, 'clusterid': ctrl_cluster_id, \
        'controllerid': ctrl_id, 'iops': POOL_IOPS, 'diskslist': allocatable_diskidlist, \
        'grouptype': POOL_TYPE}

# Pool creation step

pool_creation = create_pool(pool_params, STDURL)
if pool_creation[0] == 'FAILED':
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
           ' : %s', pool_creation[1])
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)



# Obtain the Pool list for before extracting the name

pool_list = listPool(STDURL)
if pool_list[0] == 'FAILED':
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
            ': %s', pool_list[1])
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)
pool_list = pool_list[1]

# Get the pool_info for the desired from the list obtained above

#pool_info = get_pool_info(pool_list, POOL_NAME)
pool_info = get_pool_info(pool_list, None)
if pool_info[0] == 'FAILED':
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
           ' : %s', pool_info[1])

# Extract the pool_id from the info obtained for said pool above

pool_id = pool_info[1] # Note that in get_pool_info return value, pool_info[1] itself is ID

# Get account ID for VSM creation

account_id = get_account_id(STDURL, None) # 2nd param is acc_name, if None, taken as 1st acc
if account_id[0] == 'FAILED':
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
           ': %s', account_id[1])
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)
account_id = account_id[1]

# Provide variables for VSM creation (from conf & hardcode) in dict format 

vsm_dict = {'name': VSM_NAME, 'accountid': account_id, 'poolid': \
        pool_id, 'totaliops': POOL_IOPS, 'quotasize': '1T', 'tntinterface': \
        VSM_INTERFACE, 'dnsserver': VSM_DNS, \
        'ipaddress': VSM_IP, 'totalthroughput': 4*int(POOL_IOPS)}

# Create VSM using the pool_id and the params received from conf file

result = create_tsm(vsm_dict, STDURL) # This method is an aberration, elsewhere STDURL is 1st param
if result[0] == 'FAILED':
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
            ': %s', result[1])
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)

# Get the info for the VSM created above (this list method response contains id, not create, so needed)

vsm = listTSMWithIP_new(STDURL, VSM_IP)
if vsm[0] == 'FAILED':
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
            ': %s', tsm[1])
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)
vsminfo = vsm[1]
print vsminfo
# Extract the vsm_id & vsm_dataset_id from info obtained above

vsm_id = vsminfo[0].get('id')
vsm_dataset_id = vsminfo[0].get('datasetid')

# Provide variables for Volume creation (from conf & hardcode) in dict format 

vol_dict = {'name': VOL_NAME, 'quotasize': '500G', 'tsmid': vsm_id, 'iops': POOL_IOPS, \
        'datasetid': vsm_dataset_id, 'protocoltype': 'NFS'}

# Create Volume using the vsm_ids and params specified 

result = create_volume(vol_dict, STDURL)
verify_create_volume(result)

# Get the info for the Volume created above (this list method response contains id, etc.., not create, so needed)

volumes = listVolumeWithTSMId_new(STDURL, vsm_id)
if volumes[0] == 'FAILED':
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
            ': %s', volumes[1])
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)
volumes = volumes[1]

# Extract the vol_id & vol_mnt_pt from info obtained above

for vol in volumes:
    vol_id = vol.get('id')
    vol_mnt_pt = vol.get('mountpoint')

# Updating nfs client access property for volume


result = addNFSclient(STDURL, vol_id, 'ALL')
if result[0] == 'FAILED':
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
            ': %s', result[1])
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)


# Form the command to mount, will be sent to client for execution

mkdir_cmd = 'mkdir %s' %(CLIENT_NFS_MOUNT_PNT) # Way to assign string where using %s
mount_cmd = 'mount -o mountproto=tcp,sync %s:/%s %s' %(VSM_IP, vol_mnt_pt, CLIENT_NFS_MOUNT_PNT)
check_mount_cmd = 'df -h | grep %s' %(vol_mnt_pt)

# Perform the nfs mount on the client machine

mkdir_result = sshToOtherClient(CLIENT1_IP, CLIENT1_USER, CLIENT1_PASSWORD, mkdir_cmd)
mount_result = sshToOtherClient(CLIENT1_IP, CLIENT1_USER, CLIENT1_PASSWORD, mount_cmd)
check_mount_result = sshToOtherClient(CLIENT1_IP, CLIENT1_USER, CLIENT1_PASSWORD, check_mount_cmd)
if '%s' %(vol_mnt_pt) in str(check_mount_result):
    print "Volume is mounted successfully"
else:
    print "Volume is not mounted successfully" 
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is blocked due to' \
            ': %s', mount_result)
    is_blocked(startTime, FOOTER_MSG, BLOCKED_MSG)

# Transfer the shell script that will run the workload 

#src_file = 'FileCreateReadModifyWriteDelete.sh'
#src_file = 'FileCreateReadModifyWriteDelete.py'
#dst_file = src_file
#file_transfer_result = putFileToController(CLIENT1_IP, CLIENT1_PASSWORD, src_file, dst_file)

src_file_1 = 'SmallFileCreate.py'
src_file_2 = 'SmallFileReadModify.py'
src_file_3 = 'SmallFileDelete.py'

dst_file_1 = src_file_1
dst_file_2 = src_file_2
dst_file_3 = src_file_3

file_transfer_result_1 = putFileToController(CLIENT1_IP, CLIENT1_PASSWORD, src_file_1, dst_file_1)
file_transfer_result_2 = putFileToController(CLIENT1_IP, CLIENT1_PASSWORD, src_file_2, dst_file_2)
file_transfer_result_3 = putFileToController(CLIENT1_IP, CLIENT1_PASSWORD, src_file_3, dst_file_3)

# Form the command that will run the workload on the NFS mount point

#run_workload_cmd = 'sh FileCreateReadModifyWriteDelete.sh %s' %(CLIENT_NFS_MOUNT_PNT)
#run_workload_cmd = 'nohup python FileCreateReadModifyWriteDelete.py %s' %(CLIENT_NFS_MOUNT_PNT)

run_workload_cmd_1 = 'nohup python SmallFileCreate.py %s' %(CLIENT_NFS_MOUNT_PNT)
run_workload_cmd_2 = 'nohup python SmallFileReadModify.py %s' %(CLIENT_NFS_MOUNT_PNT)
run_workload_cmd_3 = 'nohup python SmallFileDelete.py %s' %(CLIENT_NFS_MOUNT_PNT)

# Note the time when the workload starts

startTime = ctime()

# Run the File Create Read ModifyWrite Delete Ops on the NFS mount point for 5 iterations

sshToOtherClient(CLIENT1_IP, CLIENT1_USER, CLIENT1_PASSWORD, run_workload_cmd_1)
sshToOtherClient(CLIENT1_IP, CLIENT1_USER, CLIENT1_PASSWORD, run_workload_cmd_2)
sshToOtherClient(CLIENT1_IP, CLIENT1_USER, CLIENT1_PASSWORD, run_workload_cmd_3)

#sshToRemoteClient(CLIENT1_IP, CLIENT1_USER, CLIENT1_PASSWORD, run_workload_cmd)
# Note the time when the workload execution has completed

endTime = ctime()

# Grep the workload script's log file to verify successful run

test_result = sshToOtherClient(CLIENT1_IP, CLIENT1_USER, CLIENT1_PASSWORD, \
        'grep -w "CREATED\|MODIFIED\|DELETED" FileCreateReadModifyWriteDelete.log | wc -l')
if int(test_result) == 3:
    print "Workload has run successfully"
    logging.info('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is successfully completed')
    resultCollection('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is %s', \
            ['PASSED', ''], startTime, endTime)
else:
    logging.error('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is failed,' \
            'look at client logs')
    resultCollection('Testcase Continuous_File_Ops_Multiple_Small_Files_NFS is %s', \
            ['FAILED', ''], startTime, endTime)












