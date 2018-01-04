import requests
import os, shutil
from django.http import HttpResponse
from django.http import JsonResponse
from google_drive_rdm import download_from_google_drive, upload_to_google_drive, get_file_contents, set_file_contents
from github_rdm import clone_from_github, copy_from_github, push_to_github
from ftp_rdm import ftp_to_biz, ftp_from_biz
from heroku_rdm import push_from_site_to_heroku, list_apps, delete_app, create_app, add_papertrail
from url_rdm import download_from_url
from file_rdm import replace_all, write_lines_to_file

from .models import Greeting

def parse_url(request):
    r = request.POST.dict()
    print(r)
    if not r.keys():    
        r = request.GET.dict()

    if len(r.keys()) == 0:
        return list_apps()

    app_functions = {
        'delete': delete_app,
        'create': create_app,
        'addon': add_papertrail }
    for method in r.keys():
        if method in app_functions:
            return app_functions[method](r[method])

    if 'get_state' in r:
        return get_file_contents('Projects/mycloudgit/state', 'cloudgit_state.txt')

    field_name = ['field', 'replace', 'bash', 'bash_release', 'new_file']
    field_list = []
    url_field = set()
    for k in r.keys():
        for field in field_name:
            if k[:len(field)] != field: continue
            if field == 'field':
                content = r[k].replace('\n','\\n')
                url_field.add('field')
            else:
                content = r[k]
            field_list.append({'field': field, 'content': content})

    if 'field' in url_field:
        set_file_contents(
            [i['content'] for i in field_list if i['field'] == 'field'],             'Projects/mycloudgit/state', 'cloudgit_state.txt'
        )

    if 'from' not in r.keys():
        return { 'error': 'Keyword not in list.' }

    methods = {
        'github': { 'from': copy_from_github, 'to': push_to_github },
        'google_drive': { 'from': download_from_google_drive,
                          'to': upload_to_google_drive },
        'biz': { 'to': ftp_to_biz, 'from': ftp_from_biz },
        'heroku': { 'to': push_from_site_to_heroku },
        'url': { 'from': download_from_url }
    }

    # pushing to github requires that the destination repo is cloned first.
    if 'to' in r and 'github' in r['to']:
        clone_from_github(r['from_folder'], r['to_folder'])

    dir = 'from'
    for site_name in methods.keys():
        if site_name not in r[dir]: continue
        args = [r['from_folder']]
        if 'github_account' in r and site_name == 'github':
            args.append(r['github_account'])
        ''' Uncomment to allow passing of github tarball url directly to heroku
        if site_name == 'github' and 'to' in r and r['to'] == 'heroku':
            continue
        '''
        data = methods[site_name][dir](*args)

    for script in field_list:
        if script['field'] == 'replace':
            print(script['content'])
            replace_all(script['content'], r['from_folder'])

        if script['field'] == 'bash':
            os.chdir(r['from_folder'].split('/')[-1])
            for bash_command in script['content'].split('\n'):
                print(os.system(bash_command))
            print(os.listdir('.'))
            os.chdir('..')

        if script['field'] == 'bash_release':
            os.chdir(r['from_folder'].split('/')[-1])
            write_lines_to_file('release_tasks.sh', script['content'].split('\n'))
            write_lines_to_file('Procfile', ['release: bash ./release_tasks.sh'])
            os.chdir('..')

        if script['field'] == 'new_file':
            os.chdir(r['from_folder'].split('/')[-1])
            file_content = script['content'].split('-filename-')[0].split('\n')
            file_name = script['content'].split('-filename-')[1].strip()
            write_lines_to_file(file_name, file_content)
            os.chdir('..')

    dir = 'to'
    for site_name in methods.keys():
        if site_name not in r[dir]: continue
        args = [r['from_folder']]
        if 'to_folder' in r:
            args.append(r['to_folder'])
        if 'from_folder' in r:
            args[0] = r['from_folder'].split('/')[-1]
        if r['from'] == 'url':
            args[0] = '_temp'
        if 'commit_message' in r and site_name == 'github':
            args.append(r['commit_message'])
        if 'start' in r and site_name == 'google_drive':
            args.append(int(r['start']))
        if 'github_account' in r and site_name == 'heroku':
            args.append(r['github_account'])
        if site_name == 'heroku':
            args.append(r['from'])
        data = methods[site_name][dir](*args)
        if 'from' in r and 'from_folder' in r:
            shutil.rmtree(r['from_folder'])
        return data

def index(request):
    data = parse_url(request)
    response = JsonResponse(data)
    response['Access-Control-Allow-Origin'] = '*'
    return response

def db(request):
    None

