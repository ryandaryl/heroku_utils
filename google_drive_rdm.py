from __future__ import print_function
import httplib2
import os
import shutil
import csv

from apiclient import discovery
from apiclient.http import MediaIoBaseDownload, MediaFileUpload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import oauth2client
import io

file_count = None

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except:  # ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Drive API Python Quickstart'

json_string = os.environ.get('GOOGLE_DRIVE_JSON_STRING', None)

query_string = {
    'match_name_parents': "name = '{}' and '{}' in parents and trashed = false",
    'match_name': "name = '{}' and trashed = false",
    'in_parents': "'{}' in parents and trashed = false"
}

def get_service():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    return service

def delete_all_files(folder):
    if not os.path.exists(folder):
        return
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        if the_file == ".git": continue
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(e)

def get_file_data(method_name, args, data_types, count, service):
    results = service.files().list(
        q=query_string[method_name].format(*args),
        pageSize=count,
        fields="files({})".format(','.join(data_types))).execute()
    items =  results.get('files', [])
    if len(data_types) == 1:
        return [i[data_types[0]] for i in items]
    else:
        return items

def download(id,path,service,name='',mimeType='text/plain'):
    global file_count
    downloaded = False
    google_types = {
        'application/vnd.google-apps.document': 'text/plain',
        'application/vnd.google-apps.spreadsheet': 'text/csv'
    }
    file_request = None
    if mimeType in google_types:
        file_request = service.files().export_media(
                                             fileId=id,
                                             mimeType=google_types[mimeType])
    else:
        file_request = service.files().get_media(fileId=id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, file_request)
    done = False
    try:
        while done is False:
            status, done = downloader.next_chunk()
        downloaded = True
    except:
        downloaded = False
    filename = '/'.join(path + [name])
    with open(filename, 'wb+') as new_file:
        if downloaded:
            content = fh.getvalue()
        else:
            content = b''
        if content[:3] == b'\xef\xbb\xbf':
            content = content[3:]
        new_file.write(content)
    file_count += 1

def get_files(folder_obj, service, path=[]):
    folder = 'application/vnd.google-apps.folder'
    subfolders = []
    items = get_file_data('in_parents', [folder_obj['id']], ['name', 'id', 'mimeType'], 1000, service)
    if not items:
        print('No files found.')
    else:
        for item in items:
            if item['mimeType'] == folder:
                subfolders.append(item)
            else:
                item['service'] = service
                item['path'] = path
                download(**item)
    return subfolders, folder_obj['id']

def get_subfiles(subfolders, service, path=[]):
    for subfolder in subfolders:
        new_folder = '/'.join(path + [subfolder['name']])
        delete_all_files(new_folder)
        if not os.path.exists(new_folder):
            os.makedirs(new_folder)
        subfolders, parent_id = get_files(subfolder, service, path + [subfolder['name']])
        get_subfiles(subfolders, service, path + [subfolder['name']])

def get_credentials():
    """Fakes oauth process by writing the json file that normally results
    from oauth.
    """
    credential_path = os.path.join('drive-python-quickstart.json')
    with open(credential_path, 'w') as json_file:
        json_file.write(json_string)

    store = Storage(credential_path)
    credentials = store.get()
    return credentials

def download_from_google_drive(folder_path):
    service = get_service()
    parent_name, folder_name = ('/' + folder_path).split('/')[-2:]
    parent_id_list = get_file_data('match_name', [parent_name], ['id'], 1, service)
    folder_id_list = get_file_data('match_name', [folder_name], ['id', 'parents'], 1, service)
    folder_id = folder_id_list[0]['id']
    parent_id = None
    for folder in folder_id_list:
        union = list(set(parent_id_list) & set(folder['parents']))
        if len(union) > 0:
            folder_id = folder['id']
            parent_id = union[0]
    path = []
    global file_count
    file_count = 0
    get_subfiles([{'id': folder_id, 'name': folder_name}], service)
    return { 'file_count': file_count }

def is_binary(filepath):
    textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
    is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
    return is_binary_string(open(filepath, 'rb').read(1024))

def is_csv(filepath):
    allowed_delimiters = [ ',', ' ' ]
    with open(filepath) as csvfile:
        dialect = None
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=''.join(allowed_delimiters))
            csvfile.seek(0)
        except csv.Error:
            pass
        if dialect:
            reader = csv.reader(csvfile, dialect)
            columns = len(next(reader))
            rows = 0
            for row in enumerate(reader):
                rows += 1
            if (columns > 3) and (rows > 5):
                return True
    return False

def get_mimetype(filepath):
    if is_binary(filepath):
        return None
    #if is_csv(filepath):
    #    mimetype = 'spreadsheet'
    #csv detection does not work correctly.
    #Also, downloading of Google Sheets to csv introduces quotes in first line.
    else:
        mimetype = 'document'
    return mimetype

def create_file(filename,local_path,mimetype,parent,service,overwrite=False):
    if parent:
        existing = get_file_data('match_name_parents', [filename, parent], ['id'], 1, service)
        if existing:
            if overwrite:
                service.files().delete(fileId=existing[0]).execute()
            else:
                return existing[0]
        parent = [parent]
    else:
        existing = get_file_data('match_name_parents', [filename, 'root'], ['id'], 1, service)
        if existing:
            if overwrite:
                service.files().delete(fileId=existing[0]).execute()
            else:
                return existing[0]
        parent = []
    if mimetype != 'folder' and os.path.getsize(local_path) > 20 * 1000:
        mimetype = None               # Don't convert to Google Doc if file size is large (it's slow)
    file_metadata = {
      'name': filename,
      'mimeType': ('application/vnd.google-apps.' + mimetype) if mimetype else None,
      'parents': parent
    }
    kwargs = { 'body': file_metadata,
               'fields': 'id' }
    upload_mimetype = {
        'document': 'text/plain',
        'spreadsheet': 'text/csv'
    }
    if mimetype != 'folder' and os.path.getsize(local_path) > 0:
        kwargs['media_body'] = MediaFileUpload(local_path,
                        mimetype=upload_mimetype[mimetype] if mimetype in upload_mimetype else None,
                        resumable=True)
    file = service.files().create(**kwargs).execute()
    return file['id']

def upload_to_google_drive(local_dir,remote_dir,start=0,overwrite=False):
    file_count = 0
    uploaded = []
    service = get_service()
    id_dict = { 'root': None }
    for dir in remote_dir.split('/'):
        parent = id_dict['root']
        id_dict['root'] = create_file(dir, '', 'folder', parent, service)
    os.chdir(local_dir)
    for root, dirs, files in os.walk(".", topdown = True):
       for list in [dirs, files]:
           list.sort()
       if '/' not in root:
           parent = id_dict['root']
       else:
           parent = id_dict[root.split('/')[-1]]
       for name in dirs:
           id_dict[name] = create_file(name, os.path.join(root, name), 'folder', parent, service)
       for name in files:
           file_count += 1
           if file_count < start or file_count >= start + 6: continue
           filepath = os.path.join(root, name)
           id_dict[name] = create_file(name, filepath, get_mimetype(filepath), parent, service, overwrite)
           uploaded.append(name)
    os.chdir('..')
    return { 'uploaded': uploaded }

def get_file_contents(folder, filename):
    download_from_google_drive(folder)
    state_list = []
    filepath = '/'.join([folder.split('/')[-1], filename])
    with open(filepath) as fh:
        for i in fh:
            state_list.append(i[:-1] if i[-1:] == '\n' else i)
    return {'state': state_list}

def set_file_contents(data, remote_dir, filename):
    download_from_google_drive(remote_dir)
    local_dir = remote_dir.split('/')[-1]
    filepath = '/'.join([local_dir, filename])
    with open(filepath, 'w') as fh:
        fh.write('\n'.join(data))
    upload_to_google_drive(local_dir, remote_dir, 0, True)

if __name__ == '__main__':
    download_from_google_drive('Projects/mycloudgit/state/')