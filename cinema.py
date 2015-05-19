import os
import requests
import re
import shutil
from zipfile import ZipFile
from io import BytesIO
from os import path
import platform
from subprocess import call as system

log = print

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
    for f in os.listdir(target):
        if f.endswith('.srt'):
            log('Found existing subtitle at {}'.format(f))
            return path.join(target, f)
    return download_subtitles(path.basename(target), target)

def get_movie(target):
    files = [(path.getsize(path.join(target, f)), f) for f in os.listdir(target)]
    files.sort(reverse=True)
    return os.path.join(target, files[0][1])


def play(target):
    movie = get_movie(target)
    log('Using movie at {}'.format(movie))
    subtitles = get_subtitles(target)
    log('Using subtitles at {}'.format(subtitles))

    if platform.system() == 'Windows':
        system([r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe', movie, '--sub-file', subtitles])
    else:
        system([r'omxplayer', movie, '--subtitles', subtitles])

min_movie_size = 5000000
def list_movies(movies_dir):
    for item in os.listdir(movies_dir):
        full_item = path.join(movies_dir, item)
        size = path.getsize(full_item)
        if size > min_movie_size or path.isdir(full_item):
            yield full_item

def serve(movies_dir):
    from flask import Flask, redirect
    from urllib.parse import quote as urlencode
    from urllib.parse import unquote as urldecode
    app = Flask(__name__)

    @app.route("/")
    def serve_root():
        page = ['<html><body><ul>']
        for movie_path in list_movies(movies_dir):
            movie = path.basename(movie_path)
            page.append('<li><a href="view/{}">{}</a></li>'.format(urlencode(movie), movie))
        page.append('<ul></body></html>')
        return ''.join(page)

    @app.route("/view/<movie>")
    def serve_view(movie):
        template = '<html><body><h1>{}</h1><br><a href="/play/{}">Play</a></body></html>'
        return template.format(movie, urlencode(movie))

    @app.route("/play/<movie>")
    def serve_play(movie):
        play(path.join(movies_dir, movie))
        return redirect('/')

    app.run(port=80, host='0.0.0.0', debug=True)

serve(r"/media/hd250/movies")
#play(r"F:\movies\Epic (2013) [1080p]")
