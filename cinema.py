import os
from os import path
import platform
from subprocess import Popen as system_child
from subtitles import get_subtitles

log = print

def get_movie(target):
    files = [(path.getsize(path.join(target, f)), f) for f in os.listdir(target)]
    files.sort(reverse=True)
    return path.join(target, files[0][1])

def play(target):
    movie = get_movie(target)
    log('Using movie at {}'.format(movie))
    subtitles = get_subtitles(movie)
    log('Using subtitles at {}'.format(subtitles))

    if platform.system() == 'Windows':
        system_child([r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe', movie, '--sub-file', subtitles])
    else:
        os.system("echo 'on 0' | cec-client -s")
        system_child([r'omxplayer', movie, '--subtitles', subtitles, '-b'])

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

    HEAD = """<head><link rel="stylesheet" type="text/css" href="/style.css"></link><meta http-equiv="content-type" content="text/html; charset=UTF-8"></head>"""

    @app.route("/")
    def serve_root():
        page = ['<html>', HEAD, '<body><ul>']
        for movie_path in list_movies(movies_dir):
            movie = path.basename(movie_path)
            page.append('<li><a href="view/{}">{}</a></li>'.format(urlencode(movie), movie))
        page.append('<ul></body></html>')
        return ''.join(page)

    @app.route("/style.css")
    def serve_style():
        return app.send_static_file('style.css')

    @app.route("/view/<movie>")
    def serve_view(movie):
        template = '<html>' + HEAD + '<body><h1>{}</h1><br><a href="/play/{}">Play</a></body></html>'
        return template.format(movie, urlencode(movie))

    @app.route("/play/<movie>")
    def serve_play(movie):
        play(path.join(movies_dir, movie))
        return redirect('/control')

    def run_control(name):
        os.system('./dbuscontrol.sh "{}"'.format(name))

    @app.route("/control")
    def serve_control():
        template = '<html>' + HEAD + """<body>
<a href="/control/playpause">Play/Pause</a><br>
<a href="/control/subtitles">Toggle Subtitles</a><br>
<a href="/control/stop">Stop</a><br>
</body></html>"""
        return template

    @app.route("/control/playpause")
    def serve_control_playpause():
        run_control('pause')
        return redirect('/control')

    @app.route("/control/subtitles")
    def serve_control_subtitles():
        run_control('togglesubtitles')
        return redirect('/control')

    @app.route("/control/stop")
    def serve_control_stop():
        run_control('stop')
        return redirect('/')

    app.run(port=80, host='0.0.0.0', debug=True)

serve(r"/home/guest/movies")
#play(r"F:\movies\Epic (2013) [1080p]")
