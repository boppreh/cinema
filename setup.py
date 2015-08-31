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

base_image_url = request_db('/configuration')['images']['base_url'] + 'original'
def ensure_overview(movie):
    if movie.overview and movie.poster and movie.score:
        return

    response = request_db('/search/movie', {'query': movie.title})['results'][0]
    movie.overview = response['overview']
    movie.score = response['vote_average']
    with movie._poster_path().open('wb') as f:
        image_url = base_image_url + response['poster_path']
        f.write(requests.get(image_url).content)

    sleep(1)

print('Searching for movies...')
movies = Movie.search(movies_dir, fetch_length=True, debug=True)

print('Ensuring metadata...')
for movie in movies[3:]:
    print(movie)
    try: ensure_overview(movie)
    except Exception as e: print(e)
    try: movie.ensure_subtitle('pt')
    except MissingSubtitle: pass
    try: movie.ensure_subtitle('en')
    except MissingSubtitle: pass

cache_path = Path(movies_dir) / 'cache.pickle'
pickle.dump(list(sorted(movies)), cache_path.open('wb'))
