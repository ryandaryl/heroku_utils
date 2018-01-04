import requests
import json
from tar_zip_rdm import dir_to_tarfile

my_account = os.environ.get('GITHUB_USERNAME', None)

heroku_url = 'https://api.heroku.com/apps/'
heroku_path = heroku_url + '{}/{}'
github_url = "https://api.github.com/repos/{}/{}/tarball/master" 
headers = {'content-type': 'application/json',
           'Accept': 'application/vnd.heroku+json; version=3',
           'Authorization': 'Bearer ' + os.environ.get('HEROKU_AUTH', None)}

result_url = 'https://api.heroku.com/apps/start-rdm/builds/d370f8f1-43e5-4f1d-ba23-aec01b64de49/result'
#r = requests.get(result_url, headers=headers)

def upload_tar(heroku_app_name,tarfile='temp.tar'):
    r = requests.post(heroku_path.format(heroku_app_name, 'sources'), headers=headers)
    get_url = r.json()['source_blob']['get_url']
    with open(tarfile, 'rb') as fh:
        filedata = fh.read()
    file_headers = headers.copy()
    #file_headers['content-type'] = 'application/octet-stream'
    del file_headers['content-type']
    r = requests.put(r.json()['source_blob']['put_url'], data=filedata)
    return get_url

def push_to_heroku(tar_url,heroku_app_name):
    data = { "source_blob": { "url": tar_url } }
    r = requests.post(heroku_path.format(heroku_app_name, 'builds'), data=json.dumps(data), headers=headers)
    return { 'push_id': r.json()['id'], 'app_name': heroku_app_name }

def push_from_github_to_heroku(repo_name,heroku_app_name,github_account=my_account):
    print(repo_name,heroku_app_name,github_account)
    url = github_url.format(github_account, repo_name)
    return push_to_heroku(url, heroku_app_name)

def push_from_local_to_heroku(local_dir,heroku_app_name):
    dir_to_tarfile(local_dir, ignore='.git')
    tar_url = upload_tar(heroku_app_name)
    return push_to_heroku(tar_url, heroku_app_name)

def push_from_site_to_heroku(*args):
    ''' Uncomment to allow passing of github tarball url directly to heroku
    if 'github' in args:
        return push_from_github_to_heroku(*args[:-1])
    '''
    return push_from_local_to_heroku(*args[:2])

def list_apps():
    app_list = requests.get(heroku_url, headers=headers).json()
    return { 'app': [i['name'] for i in app_list] }

def delete_app(app_name):
    response = requests.delete(
             heroku_url + app_name,
             headers=headers).json()
    return { 'deleted_app': {k: response[k] for k in ('name', 'web_url')}}

def create_addon(app_name,addon,plan):
    return {
        'addon_name': requests.post(
             heroku_url + app_name + '/addons/',
             data=json.dumps({
                 'attachment': {
                     'name': addon.upper(),
                 },
                 'plan': '{}:{}'.format(addon, plan)
             }),
             headers=headers).json()['plan']['name'],
         'on_app': app_name }

def create_app(app_name):
    response = requests.post(
             heroku_url,
             data=json.dumps({'name': app_name}),
             headers=headers).json()
    items = ['name', 'web_url']
    if 'name' in response and 'web_url' in response:
        return { 'created_app': {k: response[k] for k in items}}
    else:
        return response

def add_papertrail(app_name):
    result = { 'addons': [] }
    result['addons'].append(create_addon(app_name, 'papertrail', 'choklad'))
    return result