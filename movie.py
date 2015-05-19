import os
import requests
import re
import shutil
from zipfile import ZipFile
from io import BytesIO
from os import path

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
				return member.filename

def get_subtitles(target):
	for f in os.listdir(target):
		if f.endswith('.srt'):
			log('Found existing subtitle at {}'.format(f))
			return path.join(target, f)
	return download_subtitles(path.basename(target), target)

def get_movie(target):
	files = [(os.path.getsize(path.join(target, f)), f) for f in os.listdir(target)]
	files.sort(reverse=True)
	return os.path.join(target, files[0][1])

import platform
if platform.system() == 'Windows':
	player_format = r'"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe" {} --sub-file {}'
else:
	player_format = 'omxplayer {} --subtitles {}'

def play(target):
	movie = get_movie(target)
	log('Using movie at {}'.format(movie))
	subtitles = get_subtitles(target)
	log('Using subtitles at {}'.format(subtitles))
	os.system(player_format.format(movie, subtitles))

play(r"E:\media\videos\movies\Juno[2007]DvDrip[Eng]-aXXo")