import os
from os import path
import requests
import re
from zipfile import ZipFile
from io import BytesIO
log = print

def convert_to_utf8(file_path):
    os.system('vim +"set bomb | set fileencoding=utf-8 | wq" "{}"'.format(file_path))

def download_subtitles(title='Forrest Gump', target='.'):
    page = requests.get('http://www.opensubtitles.org/pt/search2?MovieName={}&id=8&action=search&SubLanguageID=pob'.format(title))

    if '/pt/search/' in page.url:
        log('Arrived at subtitle search page.')
        format = """onclick="reLink\(event,'/pt/subtitleserve/sub/(\d+)'\);">(\d+)x"""
        results = [(int(downloads), id) for id, downloads in re.findall(format, page.text)]
        results.sort(reverse=True)
        most_popular = results[0][1]
    elif '/pt/subtitles/' in page.url:
        log('Found direct subtitle.')
        most_popular = re.search(r'/pt/subtitles/(\d+)/', page.url).groups()[0]

    log('Using subtitle id {}'.format(most_popular))

    zipbytes = requests.get("http://dl.opensubtitles.org/pt/download/sub/{}".format(most_popular)).content
    with ZipFile(BytesIO(zipbytes)) as zipfile:
        for member in zipfile.infolist():
            if member.filename.endswith('.srt'):
                zipfile.extract(member, target)
                return path.join(target, member.filename)

def get_subtitles(target):
    subtitles_path = None
    for f in os.listdir(target):
        if f.endswith('.srt'):
            log('Found existing subtitle at {}'.format(f))
            subtitles_path = path.join(target, f)
    if not subtitles_path:
        subtitles_path = download_subtitles(path.basename(target), target)
    convert_to_utf8(subtitles_path)
    return subtitles_path
