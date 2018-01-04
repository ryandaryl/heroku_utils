import os
import shutil
from ftplib import FTP

ftp = None
file_count = None

def ftp_login():
    global ftp
    #domain name or server ip:
    ftp = FTP(os.environ.get('BIZNF_URI', None))
    ftp.login(user=os.environ.get('BIZNF_USERNAME', None), passwd = os.environ.get('BIZNF_PASSWORD', None))

    #change to web-facing directory:
    ftp.cwd('/' + os.environ.get('BIZNF_USERNAME', None) + '/')

def make_dir(dir_name):
    try:
        ftp.mkd(dir_name)
    except Exception as e:
        if not e.args[0].startswith('550'): 
            raise

def upload_file(path, filename):
    global ftp
    try:
        ftp.storbinary('STOR '+filename, open('/'.join([path, filename]), 'rb'))
    except Exception as e:
        if not e.args[0].startswith('550'): 
            raise

def upload_dir(local_dir):
    global ftp
    global file_count
    for i,filename in enumerate([f for f in os.listdir(local_dir)]):
        full_path = '/'.join([local_dir, filename])
        if os.path.isfile(full_path):
            upload_file(local_dir, filename)
            file_count += 1
        else:
            if '.git' in filename:
                continue
            make_dir(filename)
            ftp.cwd(filename)
            upload_dir(full_path)
            ftp.cwd('..')

def ftp_to_biz(local_dir, remote_dir=None):
    global ftp
    global file_count
    file_count = 0
    ftp_login()
    if remote_dir:
        make_dir(remote_dir)
        ftp.cwd(remote_dir)
    upload_dir(local_dir)
    ftp.quit()
    return {'file_count' : file_count}

def download_file(filename):
    global ftp
    global file_count
    fh = open(filename, 'wb+')
    try:
        ftp.retrbinary('RETR '+ filename, fh.write)
        file_count += 1
        fh.close()
    except:
        fh.close()
        os.remove(filename)
        ftp.cwd(filename)
        download_dir(filename)
        ftp.cwd('..')

def download_dir(remote_dir):
    print(remote_dir)
    global ftp
    local_dir = remote_dir
    if os.path.exists(local_dir):
        shutil.rmtree(local_dir)
    os.mkdir(local_dir)
    os.chdir(local_dir)
    for filename in ftp.nlst():
        '''
        try:
            ftp.cwd(filename)
            download_dir(filename)
            ftp.cwd('../')
        except:
        '''
        download_file(filename)
    os.chdir('..')

def ftp_from_biz(remote_dir):
    global ftp
    global file_count
    file_count = 0
    ftp_login()
    ftp.cwd(remote_dir)
    download_dir(remote_dir)
    ftp.quit()
    return {'file_count' : file_count}