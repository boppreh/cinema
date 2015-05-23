import os
from os import path
import requests
import re
from zipfile import ZipFile
from io import BytesIO
from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def convert_to_utf8(file_path):
    os.system('vim +"set bomb | set fileencoding=utf-8 | wq" "{}"'.format(file_path))

def select_best(title, subs):
    """
    Returns the subtitle the matches the title most closely, or the most
    popular one.
    """
    # Remove extension.
    title = path.splitext(title)[0]
    to_order = []
    for i, sub_title, downloads in subs:
        sub_title = path.splitext(sub_title)[0]
        if similarity(sub_title, title) > 0.9:
            return i
        to_order.append((downloads, i))
    to_order.sort(reverse=True)
    return to_order[0][1]

def request_subtitles(title='Forrest Gump', language='pob'):
    page = requests.get('http://www.opensubtitles.org/pt/search2?MovieName={}&id=8&action=search&SubLanguageID={}'.format(title, language))

    if '/pt/search/' in page.url:
        # Arrived at search page.
        format = """<br />(?:<span title="(.+?)">[^<]+?</span>|([^<]*?))<br /><a rel="nofollow" onclick.+?/subtitleserve/sub/(\d+)'.+?(\d+)x"""
        matches = re.findall(format, page.text, re.DOTALL)
        subs = [(i, long_title or short_title, int(downloads))
                for long_title, short_title, i, downloads in matches]
        id = select_best(title, subs)
    elif '/pt/subtitles/' in page.url:
        # Arrived at direct subtitles page.
        id = re.search(r'/pt/subtitles/(\d+)/', page.url).groups()[0]

    zipbytes = requests.get("http://dl.opensubtitles.org/pt/download/sub/{}".format(id)).content
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
