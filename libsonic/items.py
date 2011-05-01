"""
This defines all the various class items, such as Album, Artist, Song, etc.
"""

from datetime import datetime

class BaseSonicItem(object):
    version = ''

class Response(BaseSonicItem):
    pass

class MusicFolder(BaseSonicItem):
    mid = ''
    name = ''

class License(BaseSonicItem):
    date = datetime.now()
    email = ''
    key = ''
    valid = False

class Playlist(BaseSonicItem):
    pid = ''
    name = ''

class CoverArt(BaseSonicItem):
    cid = ''

class User(BaseSonicItem):
    username = ''
    adminRole = False
    commentRole = False
    downloadRole = True
    jukeboxRole = False
    playlistRole = True
    podcastRole = False
    settingsRole = True
    streamRole = True
    uploadRole = True
    ldapAuthenticated = False

class ChatMessage(BaseSonicItem):
    message = ''
    date = datetime.now()
    username = ''

class Lyric(BaseSonicItem):
    artist = ''
    content = ''
    title = ''

class Artist(BaseSonicItem):
    aid = ''
    name = ''

class Album(BaseSonicItem):
    aid = ''
    artist = ''
    coverArt = 'id'
    isDir = True
    parent = 'parent id'
    title = ''

class Song(BaseSonicItem):
    sid = ''
    album = ''
    bitRate = 128
    contentType = '' # mimetype
    coverArt = 'cover art id'
    duration = 148 # in seconds
    genre = ''
    isDir = False
    isVideo = False
    parent = 'parent id'
    path = 'path/in/music/folder'
    size = 10000000 # in bytes
    suffix = 'mp3' # file extension
    title = ''
    track = 5 # track number
