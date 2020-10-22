import ovirtsdk4 as sdk
import time
import os
import subprocess
import json
import logging
import sys
import re
import socket


import windows_utils as utils

HOME_PATH = os.environ['USERPROFILE']
APP_DATA = os.environ['LOCALAPPDATA']
LOG_FOLDER = os.environ['TEMP']

CURRENT = os.getcwd()
RES_FOLDER = os.path.join(CURRENT, 'res')
CONFIG_FILE = os.path.join(RES_FOLDER, 'config.json')

LOG_FILE = os.path.join(LOG_FOLDER, 'pandora_connection.log')
logging.basicConfig(
    level=logging.INFO,
    filename=LOG_FILE,
    filemode='w',
    format='%(asctime)s | %(levelname)s | %(message)s',
)

try:
    with open(CONFIG_FILE, 'r') as file:
        CONFIG = json.load(file)
except:
    logging.exception('Load config file: ')
    sys.exit(4)

try:
    MAIN_CONFIG = CONFIG['main_config']
    QT_CONF = CONFIG['qt_config']

    POOL_NAME = MAIN_CONFIG['pool_name']
    PANDORA_API_URL = MAIN_CONFIG['pandora_api_address'].strip(' /\\')
    DOMAIN = MAIN_CONFIG['domain']
    CA_FILE = os.path.join(RES_FOLDER, MAIN_CONFIG['ca_file'].strip(' /\\'))
    ICON = os.path.join(RES_FOLDER, MAIN_CONFIG['icon'].strip(' /\\'))
    ICON_DOWNLOADS = os.path.join(RES_FOLDER, MAIN_CONFIG['icon_downloads'].strip(' /\\'))
    RDP_SOURCE_FILE = os.path.join(RES_FOLDER, MAIN_CONFIG['rdp_source_file'].strip(' /\\'))
    USER_DATA_FOLDER = os.path.join(APP_DATA, MAIN_CONFIG['user_data_folder'].strip(' /\\'))
    RDP_DESTINATION_FILE = os.path.join(USER_DATA_FOLDER, MAIN_CONFIG['rdp_destination_file'].strip(' /\\'))
    USER_DATA = os.path.join(USER_DATA_FOLDER, MAIN_CONFIG['user_data'].strip(' /\\'))
    SHARED_DISK = MAIN_CONFIG['shared_disk'].strip(' /\\')
    SHARED_FOLDER = os.path.join(HOME_PATH, MAIN_CONFIG['shared_folder'].strip(' /\\'))
    DOWNLOADS = os.path.join(SHARED_FOLDER, MAIN_CONFIG['downloads'].strip(' /\\'))
    PROFILE = os.path.join(SHARED_FOLDER, MAIN_CONFIG['profile'].strip(' /\\'))
    LINK_NAME = MAIN_CONFIG['link_name'].strip(' /\\')
    MAX_TIME_LAUNCH_VM = int(MAIN_CONFIG['max_time_launch_vm'])
except:
    logging.exception('Read config file: ')
    sys.exit(4)


def check_folder(folder):
    try:
        if not os.path.isdir(folder):
            os.mkdir(folder)
    except:
        logging.exception('check folder: ')


check_folder(USER_DATA_FOLDER)
check_folder(SHARED_FOLDER)
check_folder(DOWNLOADS)
check_folder(PROFILE)

if os.name == 'nt':
    import win_link
    
    try:
        win_link.safely_create_link(LINK_NAME, DOWNLOADS, ICON_DOWNLOADS)
    except:
        logging.exception('win link error: ')


class RdpConnect:

    def __init__(self):
        self.fullname = ''
        self.username = ''
        self.password = ''
        self.fqdn = ''
        self.port = 3389
        self.address = (self.fqdn, self.port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1)
    
    def load_data(self):
        logging.info('Load data')
        
        try:
            self.fullname, self.username = utils.get_name()
        except:
            logging.exception('get name error: ')
         
        try:
            with open(USER_DATA, 'r') as file:
                encrypt_password = file.read()
        except:     # (FileNotFoundError, IndexError)
            logging.exception('Load data file error: ')
            encrypt_password = ''
        
        if encrypt_password:
            try:
                self.password = utils.decrypt_data(encrypt_password)
            except:
                logging.exception('Decrypt data: ')
                self.password = ''
            
        return self.fullname, self.username, self.password

    def save_data(self, password):
        logging.info('Save data')
        self.password = password

        try:
            encrypt_password = utils.encrypt_data(self.password)
        except:
            logging.exception('Encrypt data: ')
            encrypt_password = ''

        try:
            with open(USER_DATA, 'w') as file:
                file.write(encrypt_password)
        except:
            logging.exception('Write data file: ')
    
    def connect(self):
        logging.info('Connect to ovirt')
        logging.info(f'username: {self.username}')
        try:
            connection = sdk.Connection(
                url=PANDORA_API_URL,
                username=self.username,
                password=self.password,
                ca_file=CA_FILE,
                # insecure=True,
                # debug=True,
            )
        except sdk.Error:
            logging.exception('Connection error: ')
            return 3
        except:
            logging.exception('Unexpected Connection error: ')
            return 3

        system_service = connection.system_service()
        pools_service = system_service.vm_pools_service()
        try:
            pool_service = pools_service.list(search='name={}'.format(POOL_NAME))[0]
        except sdk.AuthError:
            logging.exception('Bad credentials: ')
            connection.close()
            return 2
        except (sdk.ConnectionError, sdk.Error, IndexError):
            logging.exception('Connection error: ')
            connection.close()
            return 3
        except:
            logging.exception('Unexpected connection error: ')
            connection.close()
            return 3
        pool = pools_service.pool_service(pool_service.id)
        logging.info(f'Pool id: {pool_service.id}')

        vms_service = system_service.vms_service()
        for i in range(MAX_TIME_LAUNCH_VM):
            vms = vms_service.list(search=f'name={POOL_NAME}*')
            if len(vms):
                vm = vms[0]
                self.fqdn = vm.fqdn

                vm_service = vms_service.vm_service(vm.id)
                if vm.status == 'down':
                    vm_service.start()

                logging.info(f'VM id: {vm.id}, fqdn: {self.fqdn}')

                if re.search('int.*' + DOMAIN, self.fqdn, re.IGNORECASE):
                    self.address = (self.fqdn, self.port)
                    try:
                        self.socket.connect(self.address)
                    except socket.timeout:
                        logging.info('RDP closed')   # wait 1 sec if rdp is close (socket_timeout = 1 sec)
                        continue
                    except:
                        logging.exception('Unexpected socket error: ')
                        time.sleep(1)
                        continue
                    else:
                        logging.info('RDP OK')
                        break
                else:
                    logging.info('VM fqdn not valid')
            else:
                logging.info('Allocating vm...')
                try:
                    pool.allocate_vm()
                except sdk.Error:
                    logging.exception('Allocation error: ')

            time.sleep(1)
        else:
            logging.error('Timeout vm preparation or Can`t find allocated VM')
            connection.close()
            return 3

        connection.close()

        try:
            with open(RDP_SOURCE_FILE, 'r') as file:
                rdp_text = file.read().format(self.fqdn, SHARED_DISK)
            with open(RDP_DESTINATION_FILE, 'w') as file:
                file.write(rdp_text)
        except:
            logging.exception('Load config file: ')
            return 3

        logging.info('End connection')
        return 1

    def run_rdp_console(self):
        logging.info('Exec cmd programs')

        cmd_map_folder = ['subst', SHARED_DISK, SHARED_FOLDER]
        logging.info(f'Map folder: {cmd_map_folder}')
        try:
            ans_map_folder = subprocess.check_output(cmd_map_folder)
        except subprocess.CalledProcessError:
            logging.exception('map folder error:')
        else:
            logging.info(f'Map folder answer: {ans_map_folder}')

        cmd_add_pass = ['cmdkey', '/add:' + self.fqdn, '/user:' + self.username, '/pass:' + self.password]
        logging.info(f'Add pass... FQDN: {self.fqdn}')
        try:
            ans_add_pass = subprocess.check_output(cmd_add_pass)
        except subprocess.CalledProcessError:
            logging.exception('add pass error:')
        else:
            logging.info(f'Add pass answer: {ans_add_pass}')

        cmd_rdp = ['mstsc', RDP_DESTINATION_FILE]
        logging.info(f'Rdp: {cmd_rdp}')
        try:
            ans_rdp = subprocess.check_output(cmd_rdp)
        except subprocess.CalledProcessError:
            logging.exception('rdp error:')
        else:
            logging.info(f'RDP answer: {ans_rdp}')

        cmd_del_pass = ['cmdkey', '/delete:' + self.fqdn]
        logging.info(f'Del pass: {cmd_del_pass}')
        try:
            ans_del_pass = subprocess.check_output(cmd_del_pass)
        except subprocess.CalledProcessError:
            logging.exception('del pass error:')
        else:
            logging.info(f'Del pass answer: {ans_del_pass}')

        cmd_unmap_folder = ['subst', SHARED_DISK, '/d']
        logging.info(f'Unmap folder: {cmd_unmap_folder}')
        try:
            ans_unmap_folder = subprocess.check_output(cmd_unmap_folder)
        except subprocess.CalledProcessError:
            logging.exception('unmap folder error:')
        else:
            logging.info(f'Unmap folder answer: {ans_unmap_folder}')


if __name__ == '__main__':
    target = input()
    if target:
        pass
        # username = str(input("username : "))
        # password = str(input("password : "))

    else:
        pass
