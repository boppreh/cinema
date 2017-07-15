from cinema import Movie
from pathlib import Path
import sys

movie = Movie(Path(sys.argv[1]))
movie.download_subtitle('pt')
