from urllib.parse import quote as urlencode, unquote as urldecode
from cinema import Movie, load_cached_movies, MissingSubtitle
import requests
import json
from time import sleep
import pickle
from pathlib import Path

movies_dir = r"/media/250gb/movies"

db_key = open('themoviedb-api.txt').read().strip()

def request_db(path, params={}):
    query = '&'.join(key + '=' + urlencode(value) for key, value in params.items())
    url = 'https://api.themoviedb.org/3{}?{}&api_key={}'.format(path, query, db_key)
    return json.loads(requests.get(url).text)

configuration = request_db('/configuration')
poster_sizes = configuration['images']['poster_sizes']
assert 'original' in poster_sizes
base_image_url = configuration['images']['base_url']

def try_download_image(size, final_url, path):
    print('Trying to download image {} with size {} ({}).'.format(final_url, size, path.name))
    assert size in poster_sizes
    response = requests.get(base_image_url + size + '/' + final_url)
    if response.status_code == 200:
        with path.open('wb') as f:
            f.write(response.content)
            return True
    return False

def ensure_overview(movie):
    if movie.overview and movie.poster and movie.score and movie.thumbnail and movie.backdrop:
        return

    response = request_db('/search/movie', {'query': movie.title})['results'][0]
    movie.overview = response['overview']
    movie.score = response['vote_average']

    if movie.poster: movie.poster.unlink()
    if movie.thumbnail: movie.thumbnail.unlink()
    if movie.backdrop: movie.thumbnail.unlink()

    try_download_image('original', response['poster_path'], movie._poster_path())
    for size in poster_sizes:
        success = try_download_image(size, response['poster_path'], movie._thumbnail_path())
        if success:
            break
    try_download_image('original', response['backdrop_path'], movie._backdrop_path())

    sleep(0.3)

print('Searching for movies...')
#movies = Movie.search(movies_dir, fetch_length=True, debug=True)
movies = load_cached_movies(movies_dir)

print('Ensuring metadata...')
for movie in movies[3:]:
    print(movie)
    try: ensure_overview(movie)
    except Exception as e: print('--ERROR:', e)
    try: movie.ensure_subtitle('pt')
    except MissingSubtitle: pass
    try: movie.ensure_subtitle('en')
    except MissingSubtitle: pass

cache_path = Path(movies_dir) / 'cache.pickle'
pickle.dump(list(sorted(movies)), cache_path.open('wb'))
