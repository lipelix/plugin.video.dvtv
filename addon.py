# -*- coding: utf-8 -*- 
from __future__ import unicode_literals
import sys
from urllib import (
    urlencode,
    unquote,
)
from urlparse import parse_qsl
import xbmc
import xbmcgui
import xbmcplugin
from sources_service import (
    fetch_video_sources,
    fetch_video,
    fetch_video_formats,
    clean_video_folder,
)

_url = sys.argv[0]
_handle = int(sys.argv[1])

def get_url(**kwargs):    
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def list_videos():
    xbmcplugin.setPluginCategory(_handle, 'News')
    xbmcplugin.setContent(_handle, 'videos')

    video_sources = fetch_video_sources()

    for video_source in video_sources:
        list_item = xbmcgui.ListItem(label=video_source['name'])
        list_item.setInfo('video', {'title': video_source['name'], 'genre': video_source['genre'], 'premiered': video_source['premiered'], 'mediatype': 'video'})
        list_item.setArt({'thumb': video_source['thumb'], 'icon': video_source['thumb'], 'fanart': video_source['thumb']})
        list_item.setProperty('IsPlayable', 'true')
        url = get_url(action='play', video=video_source['video'])
        is_folder = False
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.endOfDirectory(_handle, True, True, False)

def play_video(path):
    link = unquote(path).decode('utf8')
    dialog = xbmcgui.Dialog()
    
    formats = fetch_video_formats(link)
    formatKey = dialog.select('Choose a quality', formats['format_names'])
    if (formatKey == -1):
        return

    format =  formats['format_ids'][formatKey]
    video = fetch_video(link, format)
    xbmc.log('Play video: {format} {video}'.format(format=format, video=video), xbmc.LOGINFO)
    play_item = xbmcgui.ListItem(path=video)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'play':
            play_video(params['video'])
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_videos()
        clean_video_folder()


if __name__ == '__main__':    
    router(sys.argv[2][1:])