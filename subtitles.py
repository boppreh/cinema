import os
from os import path
import requests
import re
from zipfile import ZipFile
from io import BytesIO

def convert_to_utf8(file_path):
    os.system('vim +"set bomb | set fileencoding=utf-8 | wq" "{}"'.format(file_path))

def request_subtitles(title='Forrest Gump', language='pob'):
    page = requests.get('http://www.opensubtitles.org/pt/search2?MovieName={}&id=8&action=search&SubLanguageID={}'.format(title, language))

    if '/pt/search/' in page.url:
        # Arrived at search page.
        format = """onclick="reLink\(event,'/pt/subtitleserve/sub/(\d+)'\);">(\d+)x"""
        results = [(int(downloads), id) for id, downloads in re.findall(format, page.text)]
        results.sort(reverse=True)
        most_popular = results[0][1]
    elif '/pt/subtitles/' in page.url:
        # Arrived at direct subtitles page.
        most_popular = re.search(r'/pt/subtitles/(\d+)/', page.url).groups()[0]

    zipbytes = requests.get("http://dl.opensubtitles.org/pt/download/sub/{}".format(most_popular)).content
    with ZipFile(BytesIO(zipbytes)) as zipfile:
        for member in zipfile.infolist():
            if member.filename.endswith('.srt'):
                return zipfile.open(member).read()

def download_subtitles(title, target, language='pob'):
    file_path = path.join(target, title + '.srt')
    with open(file_path, 'wb') as file:
        file.write(request_subtitles(title, language))
    return file_path

def find_existing(target):
    for f in os.listdir(target):
        if f.endswith('.srt'):
            log('Found existing subtitle at {}'.format(f))
            return path.join(target, f)

def get_subtitles(target):
    subs = find_existing(target) or download_subtitles(path.basename(target), target)
    convert_to_utf8(subs)
    return subs

if __name__ == '__main__':
    from sys import argv
    if len(argv) == 2:
        get_subtitles(argv[1])
    else:
        print("Usage: subtitles.py movie_path")
