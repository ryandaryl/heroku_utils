import requests
import os
import shutil

def download_from_url(url):
    filename = url.split('/')[-1]
    if '_temp' in os.listdir('.'):
        shutil.rmtree('_temp')
    os.makedirs('_temp')
    response = requests.get(url, stream=True)
    with open('/'.join(['_temp', filename]), 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response