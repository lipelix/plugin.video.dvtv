# -*- coding: utf-8 -*- 
from __future__ import unicode_literals
import feedparser
import re
import youtube_dl
import hashlib
import os
import xbmcaddon
import xbmc
import xbmcgui

import datetime
import time
#fix for datatetime.strptime returns None
class proxydt(datetime.datetime):
    def __init__(self, *args, **kwargs):
        super(proxydt, self).__init__(*args, **kwargs)

    @classmethod
    def strptime(cls, date_string, format):
        return datetime(*(time.strptime(date_string, format)[0:6]))

datetime.datetime = proxydt
from datetime import datetime


_videos_dir = os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode("utf-8"), 'videos')
_progress_dialog = xbmcgui.DialogProgress()

def clean_video_folder():
    xbmc.log('Clean video folder {exists}: {path}'.format(path=_videos_dir, exists=os.path.exists(_videos_dir)), xbmc.LOGWARNING)
    if os.path.exists(_videos_dir):
        map(os.unlink, (os.path.join(_videos_dir,f) for f in os.listdir(_videos_dir)))

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)

def my_hook(d):
    if d['status'] == 'downloading':
        if ('total_bytes' in d):
            percent = float(d['downloaded_bytes'])/float(d['total_bytes'] or inf)*100
        elif ('total_bytes_estimate' in d):
            percent = float(d['downloaded_bytes'])/float(d['total_bytes_estimate'] or inf)*100
        else:
            percent = 0
        _progress_dialog.update(int(percent))
    if d['status'] == 'finished':
        xbmc.log('Done downloading {filename}, now converting ...'.format(filename=d['filename']), xbmc.LOGINFO)
        _progress_dialog.close()

def item_mapper(item):
    content = item.content[0].value
    thumbnail_match = re.search("src=\"(.*?)\"", content)
    thumbnail = thumbnail_match.group(1)
    xbmc.log('Fetching item: {item}'.format(item=item), xbmc.LOGINFO)
    time_struct = item.published_parsed
    
    return {
        'name': item.title,
        'video': item.link,
        'thumb': thumbnail,
        'premiered': item.published,
        'genre': 'news',
    }

def format_filter(format):
    return format['ext'] == 'mp4'

def fetch_video_sources():
    parsed_feed = feedparser.parse('https://video.aktualne.cz/rss/dvtv/')
    sources = map(item_mapper, parsed_feed.entries)
    return sources

def fetch_video(link, format):
    xbmc.log('Fetching video: {link}'.format(link=link), xbmc.LOGINFO)
    filename = '{id}.mp4'.format(id = hashlib.md5('{link}{format}'.format(link=link, format=format)).hexdigest())
    path = os.path.join(_videos_dir, filename)
    ydl_opts = {
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
        'outtmpl': path,
        'format': format,
        'no_color': True,
    }
    _progress_dialog.create('Načítání', 'Už se to připravuje..')
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])
        xbmc.log('Video fetched: {path}'.format(path=path), xbmc.LOGINFO)
        return path

def fetch_video_formats(link):
    xbmc.log('Fetching video formats: {link}'.format(link=link), xbmc.LOGINFO)
    ydl_opts = {
        'logger': MyLogger(),
        'no_color': True,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
        formats = filter(format_filter, info['formats'])
        xbmc.log('Video formats: {formats}'.format(formats=formats), xbmc.LOGINFO)
        return {
            'format_names': map(lambda format: format['format'], formats),
            'format_ids': map(lambda format: format['format_id'], formats),
        }
