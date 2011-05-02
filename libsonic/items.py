"""
This defines all the various class items, such as Album, Artist, Song, etc.
"""

from datetime import datetime
import weakref

class BaseSonicItem(object):
    def __init__(self):
        self._postInit()

    def _postInit(self):
        pass

class Response(Response):
    def __init__(self , respDict , weakSonObj , weakParent=None):
        super(Response , self).__init__()
        self._setAttrItems(respDict)
        self._weakParent = weakParent
        self._weakSonObj = weakSonObj
        self.fh = None

    def __getattr__(self , name):
        # Do the weak reference calls
        if name == 'conn':
            return self._weakSonObj()
        if name == 'parent' and self._weakParent is not None:
            return self._weakParent()
        raise AttributeError(name)

    def _setAttrItems(self , d):
        for k , v in d.iteritems():
            setattr(self , k , v)
    
class MusicFolder(Response):
    def __getattr__(self , name):
        try:
            super(MusicFolder , self).__getattr__(name)
        except AttributeError:
            if name == 'artists':
                self.artists = self._getArtists()
                return self.artists

    def _getArtists(self):
        pass

class License(Response):
    date = datetime.now()
    email = ''
    key = ''
    valid = False

class Playlist(Response):
    pid = ''
    name = ''

class CoverArt(Response):
    cid = ''

class User(Response):
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

class ChatMessage(Response):
    message = ''
    date = datetime.now()
    username = ''

class Lyric(Response):
    artist = ''
    content = ''
    title = ''

class Artist(Response):
    aid = ''
    name = ''

class Album(Response):
    aid = ''
    artist = ''
    coverArt = 'id'
    isDir = True
    parent = 'parent id'
    title = ''

class Song(Response):
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
