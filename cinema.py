from pathlib import Path
import os
import platform
from subprocess import Popen as system_child, PIPE
import requests
import hashlib
import re
import json
import pickle

class MissingSubtitle(Exception): pass

ALL_LANGUAGES = ['pt', 'en']

class MissingSubtitle(Exception): pass

class Movie(object):
    min_movie_size = 90000000

    @staticmethod
    def search(root_path, fetch_length=True,debug=False):
        root = Path(root_path)
        def search_videos():
            yield from root.glob('**/*.avi')
            yield from root.glob('**/*.mkv')
            yield from root.glob('**/*.mp4')

        results = []
        for video in search_videos():
            if video.stat().st_size < Movie.min_movie_size:
                continue

            movie = Movie(video, length=None if fetch_length else 0)

            if debug:
                print(movie)

            results.append(movie)
        return results

    def __init__(self, video, length=None):
        self.video = video
        self.subtitles = {}
        self.title = self.video.stem
        try:
            self.length = length if length is not None else self.get_length()
        except Exception:
            self.length = 0

        for language in ALL_LANGUAGES:
            path = self._subtitle_path(language)
            if path.exists():
                self.subtitles[language] = path

    @property
    def movie_hash(self):
        readsize = 64 * 1024
        with self.video.open('rb') as f:
            self.video.stat().st_size
            data = f.read(readsize)
            f.seek(-readsize, os.SEEK_END)
            data += f.read(readsize)
        return hashlib.md5(data).hexdigest()

    def get_length(self):
        result = system_child(['avprobe', '-loglevel', 'quiet', '-show_format', '-of', 'json',
                               str(self.video)],
                               stdout=PIPE)
        return float(json.loads(result.stdout.read().decode('utf-8'))['format']['duration'])

    def _subtitle_path(self, language):
        return self.video.with_name('{}-{}.srt'.format(self.video.stem, language))

    def ensure_subtitle(self, language):
        if language not in self.subtitles:
            self.download_subtitle(language)

    def download_subtitle(self, language):
        path = self._subtitle_path(language)

        url = 'http://api.thesubdb.com/?action=download&hash={}&language={}'.format(self.movie_hash, language)
        user_agent = 'SubDB/1.0 (Pyrrot/0.1; http://github.com/jrhames/pyrrot-cli)'
        response = requests.get(url, headers={'user-agent': user_agent})
        if response.status_code != 200:
            raise MissingSubtitle('Download from thesubdb returned {} for video {} ({})'.format(response.status_code, self.video, language))
        if not response.text:
            raise MissingSubtitle('Download from thesubdb returned empty response for video {} ({})'.format(self.video, language))
        assert len(response.text)

        with path.open('w') as f:
            f.write(response.text)

        self.subtitles[language] = path

    def play(self, language=None):
        return Player(self.video, self.subtitles[language] if language else None)

    def __repr__(self):
        return 'Movie({}, {} minutes, subttiles={})'.format(self.title, self.length // 60, self.subtitles.keys())

    def __lt__(self, other):
        return self.title < other.title

class Player(object):
    def __init__(self, video, subtitle):
        self.video = str(video)
        self.subtitle = str(subtitle)
        self._start()

    def _start(self):
        # Turn TV on.
        os.system("echo 'on 0' | cec-client -s")
        if self.subtitle:
            self.subprocess = system_child([r'omxplayer', self.video, '-b'])
        else:
            self.subprocess = system_child([r'omxplayer', self.video, '--subtitles', self.subtitle, '-b'])

    def _send_command(self, name, param=None):
        if param is None:
            os.system('./dbuscontrol.sh "{}"'.format(name))
        else:
            os.system('./dbuscontrol.sh "{}" "{}"'.format(name, param))

    def play_pause(self): self._send_command('pause')
    def show_subtitles(self): self._send_command('showsubtitles')
    def hide_subtitles(self): self._send_command('hidesubtitles')
    def stop(self): self._send_command('stop')
    def set_volume(self, value): self._send_command('volume', value)
    def set_position(self, value): self._send_command('setposition', value)

player = None
movie_playing = None
def serve(movies):
    movie_playing = None

    from flask import Flask, redirect, send_from_directory
    from urllib.parse import quote as urlencode
    from urllib.parse import unquote as urldecode
    app = Flask(__name__, static_url_path='/static')
    template = """
<html>
    <head>
        <link rel="stylesheet" type="text/css" href="/static/style.css" />
        <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
        <meta name="viewport" content="width=device-width" />
        <script src="/static/script.js" type="text/javascript"></script>
    </head>
    <body>
{}
    </body>
</html>"""

    @app.route("/static/<path:path>")
    def serve_style(path):
        return send_from_directory(path)

    @app.route("/")
    def serve_root():
        if player is not None:
            return redirect('/controller')

        parts = []
        for movie in movies:
            flags = ''.join(map('<img src="/static/{}.png">'.format, movie.subtitles))
            duration = '{}:{:02}h'.format(int(movie.length / 60 / 60),
                                      int(movie.length / 60 % 60))
            parts.append('<li><a href="/movies/{}/view">{}</a> {} {}</li>'.format(urlencode(movie.title), movie.title, duration, flags))
        return template.format('<ul>' + '\n'.join(parts) + '</ul>')

    @app.route("/movies/<title>/view")
    def view(title):
        movie, = [movie for movie in movies if movie.title == title]
        parts = ['<h1>{} ({} minutes)</h1>'.format(movie.title, int(movie.length / 60))]
        for language in ALL_LANGUAGES:
            parts.append('<a href="/movies/{}/play/{}">Play <img src="/static/{}.png"></a>'.format(urlencode(movie.title), language, language))
        parts.append('<a href="/movies/{}/play/none">Play without subtitles</a>'.format(urlencode(movie.title)))
        return template.format('<br>'.join(parts))

    @app.route("/movies/<title>/play/<language>")
    def play(title, language):
        global player
        if player:
            player.stop()
        global movie_playing
        movie_playing, = [movie for movie in movies if movie.title == title]
        player = movie_playing.play(language if language != 'none' else None)
        return redirect('/controller')

    @app.route("/controller")
    def controller():
        return template.format("""
Now playing {}<br><br>

<a href="#" onclick="post('play_pause');">Play/Pause</a><br>
<a href="#" onclick="post('show_subtitles');">Show subtitles</a> / <a href="#" onclick="post('hide_subtitles');">Hide subtitles</a><br>
<a href="#" onclick="post('stop');">Play/Pause</a><br>
        """.format(movie_playing.title))

    @app.route("/controller/<command>", methods=["POST", "GET"])
    @app.route("/controller/<command>/<value>", methods=["POST", "GET"])
    def receive_command(command, value=None):
        if value is not None:
            getattr(player, command)(value)
        else:
            getattr(player, command)()

    app.run(port=8080, host='0.0.0.0', debug=True)

if __name__ == '__main__':
    """
    for movie in Movie.search(r"/media/250gb/movies", fetch_length=False):
        print(movie)
        try: movie.ensure_subtitle('pt')
        except MissingSubtitle: pass
        try: movie.ensure_subtitle('en')
        except MissingSubtitle: pass
        print(movie)
    """

    movies_dir = r"/media/250gb/movies"

    cache_path = Path(movies_dir) / 'cache.pickle'
    if cache_path.exists():
        movies = pickle.load(cache_path.open('rb'))
    else:
        movies = list(sorted(Movie.search(movies_dir, debug=True)))
        pickle.dump(movies, cache_path.open('wb'))

    serve(movies)
