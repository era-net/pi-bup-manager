import os
import sys
import configparser
import warnings
from cryptography.utils import CryptographyDeprecationWarning
with warnings.catch_warnings(action="ignore", category=CryptographyDeprecationWarning):
    import paramiko
import time
from getpass import getpass
from stat import S_ISDIR
import zipfile
from tqdm import tqdm
import shutil

class BupManager():
    def __init__(self, config_section: str = None, port: int = 22) -> None:
        if os.path.isfile('config.ini') and config_section != None:
            name = config_section.lower().replace(' ', '-')

            # read config if exists
            conf = configparser.RawConfigParser()
            conf.read('config.ini')
            conf_items = dict(conf.items(config_section))
            hostname = conf_items['hostname']
            username = conf_items['username']
            pwd = conf_items['password']

            try:
                remote_directory = conf_items['remote_path']
            except KeyError:
                remote_directory = '/home/pi'

            if pwd == 'getpass':
                print(f'[{config_section}]')
                password = getpass('Password: ')
            else:
                password = pwd
        else:
            name = 'rpi'
            # handle missing config file
            hostname = input('Hostname: ')
            username = input('Username: ')
            password = getpass('Password: ')
            remote_directory = '/home/pi'
        
        self.port = port

        self.name = name

        self.hostname = hostname
        self.username = username
        self.password = password

        self.total_items = 0

        self.recursive_count = 0

        self.remote_path = remote_directory

        self.local_path = os.path.join(os.getcwd(), 'rpi', self.remote_path.split('/')[-1])

        self.archive_filepath = None

        self.ensure_connection()

    def ensure_connection(self):
        print('\rchecking connection ... ', end='')
        try:
            transport = paramiko.Transport((self.hostname, self.port))
            transport.connect(username=self.username, password=self.password)
            transport.close()
        except:
            print('failed!')
            raise ValueError('Unable to connect. Please ensure your configuration data is correct and/or enable ssh on your pi.')
        
        print('success!')
    
    def bup(self):
        transport = paramiko.Transport((self.hostname, self.port))
        transport.connect(username=self.username, password=self.password)
        self.sftp = paramiko.SFTPClient.from_transport(transport)

        self.__set_total_count(self.remote_path) # calculating total items recursively

        self.__recursive_download(self.remote_path, self.local_path) # download recursively

        print(f'\n\ntree \'{self.remote_path}\' mirrored successfully!\n')

        # close sftp connection
        self.sftp.close()
        transport.close()

    def archive_tree(self):
        tree = 'rpi'

        # check if the tree to be archived exists
        if not os.path.isdir(tree):
            raise FileNotFoundError(f'There is nothing to be archived. \'/{tree}\' tree doesn\'t exist.')

        timestamp = time.strftime('%d-%m', time.localtime())
        arch_name = f'{self.name}-{timestamp}.zip'
        arch_path = os.path.join(os.getcwd(), arch_name)

        with zipfile.ZipFile(arch_path, 'w', zipfile.ZIP_DEFLATED) as zip:
            # list all files to zip
            files_list = []
            for root, dirs, files in os.walk(tree):
                for file in files:
                    files_list.append(os.path.join(root, file))
            
            # create a progress bar with the total number of files
            for file_path in tqdm(files_list, desc='archiving', unit='file'):
                # adding the file
                zip.write(file_path, os.path.relpath(file_path, tree))

        print('\ncleaning up ...')
        shutil.rmtree(tree)

        print(f'\narchive saved: {arch_path}\n')

    def __recursive_download(self, remote_dir, local_dir):
        # create local directory if it doesn't exist
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        # list all files and directories in the remote directory
        for item in self.sftp.listdir_attr(remote_dir):
            remote_path = os.path.join(remote_dir, item.filename)
            local_path = os.path.join(local_dir, item.filename)

            remote_path = remote_path.replace('\\', '/')

            # save only if the file or dir doesn't start with '.'
            path = remote_path.split('/')[-1]
            if not path.startswith('.'):
                self.recursive_count += 1
                if S_ISDIR(item.st_mode): # if the item is a directory
                    if path != '__pycache__': # ignore pycache
                        self.__recursive_download(remote_path, local_path)
                else: # if the item is a file, download it
                    sys.stdout.write('\x1b[2K') # clear output
                    self.sftp.get(remote_path, local_path, callback=lambda *args: self.progress_callback(*args, remote_path)) # download the file
    
    def progress_callback(self, transferred:int, total:int, remote_path: str):
        perc = f'{(transferred / total) * 100:.0f}'
        print(f'downloading [{self.recursive_count}/{self.total_items}]: {remote_path} {perc}%', end='\r')
    
    def __set_total_count(self, remote_dir: str):
        # iterate over the remote path recursively to count the total items
        for item in self.sftp.listdir_attr(remote_dir):
            # for each file
            path = os.path.join(remote_dir, item.filename)
            path = path.replace('\\', '/')

            # count only if the item doesn't start with '.'
            path_item = path.split('/')[-1]
            if not path_item.startswith('.'):
                self.total_items += 1
                if S_ISDIR(item.st_mode): # if the item is a directory
                    if path_item != '__pycache__':
                        self.__set_total_count(path) # recurse into the directory