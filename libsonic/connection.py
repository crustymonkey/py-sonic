"""
This file is part of py-sonic.

py-sonic is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

py-sonic is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with py-sonic.  If not, see <http://www.gnu.org/licenses/>
"""

from base64 import b64encode
from urllib import urlencode
from errors import *
from pprint import pprint
from cStringIO import StringIO
import json , urllib2, httplib, socket, ssl

API_VERSION = '1.8.0'


class HTTPSConnectionV3(httplib.HTTPSConnection):
    def __init__(self, *args, **kwargs):
        httplib.HTTPSConnection.__init__(self, *args, **kwargs)
        
    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        try:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv3)
        except ssl.SSLError, e:
            print("Trying SSLv3.")
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv23)           

class HTTPSHandlerV3(urllib2.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(HTTPSConnectionV3, req)
# install opener
urllib2.install_opener(urllib2.build_opener(HTTPSHandlerV3()))


class PysHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
    """
    This class is used to override the default behavior of the 
    HTTPRedirectHandler, which does *not* redirect POST data
    """
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        m = req.get_method()
        if (code in (301, 302, 303, 307) and m in ("GET", "HEAD")
            or code in (301, 302, 303) and m == "POST"):
            newurl = newurl.replace(' ', '%20')
            newheaders = dict((k,v) for k,v in req.headers.items()
                              if k.lower() not in ("content-length", "content-type")
                             )
            data = None
            if req.has_data():
                data = req.get_data()
            return urllib2.Request(newurl,
                           data=data,
                           headers=newheaders,
                           origin_req_host=req.get_origin_req_host(),
                           unverifiable=True)
        else:
            raise urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp)

class Connection(object):
    def __init__(self , baseUrl , username , password , port=4040 , 
            serverPath='/rest' , appName='py-sonic' , apiVersion=API_VERSION):
        """
        This will create a connection to your subsonic server

        baseUrl:str         The base url for your server. Be sure to use 
                            "https" for SSL connections
                            ex: http://subsonic.example.com
        username:str        The username to use for the connection
        password:str        The password to use for the connection
        port:int            The port number to connect on.  The default for
                            unencrypted subsonic connections is 4040
        serverPath:str      The base resource path for the subsonic views.
                            This is useful if you have your subsonic server
                            behind a proxy and the path that you are proxying
                            is differnt from the default of '/rest'.
                            Ex: 
                                serverPath='/path/to/subs'
                                
                              The full url that would be built then would be
                              (assuming defaults and using "example.com" and
                              you are using the "ping" view):

                                http://example.com:4040/path/to/subs/ping.view
        appName:str         The name of your application.
        apiVersion:str      The API version you wish to use for your 
                            application.  Subsonic will throw an error if you
                            try to use/send an api version higher than what
                            the server supports.  See the Subsonic API docs
                            to find the Subsonic version -> API version table.
                            This is useful if you are connecting to an older
                            version of Subsonic.
        """
        self._baseUrl = baseUrl
        self._username = username
        self._rawPass = password
        self._port = int(port)
        self._apiVersion = apiVersion
        self._appName = appName
        self._serverPath = serverPath.strip('/')
        self._opener = self._getOpener(self._username , self._rawPass)

    # Properties
    def setBaseUrl(self , url):
        self._baseUrl = url
        self._opener = self._getOpener(self._username , self._rawPass)
    baseUrl = property(lambda s: s._baseUrl , setBaseUrl)

    def setPort(self , port):
        self._port = int(port)
    port = property(lambda s: s._port , setPort)

    def setUsername(self , username):
        self._username = username
        self._opener = self._getOpener(self._username , self._rawPass)
    username = property(lambda s: s._username , setUsername)

    def setPassword(self , password):
        self._rawPass = password
        # Redo the opener with the new creds
        self._opener = self._getOpener(self._username , self._rawPass)
    password = property(lambda s: s._rawPass , setPassword)

    apiVersion = property(lambda s: s._apiVersion)

    def setAppName(self , appName):
        self._appName = appName
    appName = property(lambda s: s._appName , setAppName)

    def setServerPath(self , path):
        self._serverPath = path.strip('/')
    serverPath = property(lambda s: s._serverPath , setServerPath)

    # API methods
    def ping(self):
        """
        since: 1.0.0
        
        Returns a boolean True if the server is alive, False otherwise
        """
        methodName = 'ping'
        viewName = '%s.view' % methodName

        req = self._getRequest(viewName)
        try:
            res = self._doInfoReq(req)
        except:
            return False
        if res['status'] == 'ok':
            return True
        elif res['status'] == 'failed':
            raise getExcByCode(res['error']['code'])
        return False

    def getLicense(self):
        """
        since: 1.0.0

        Gets details related to the software license

        Returns a dict like the following:

        {u'license': {u'date': u'2010-05-21T11:14:39',
                      u'email': u'email@example.com',
                      u'key': u'12345678901234567890123456789012',
                      u'valid': True},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getLicense'
        viewName = '%s.view' % methodName

        req = self._getRequest(viewName)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getMusicFolders(self):
        """
        since: 1.0.0

        Returns all configured music folders

        Returns a dict like the following:

        {u'musicFolders': {u'musicFolder': [{u'id': 0, u'name': u'folder1'},
                                    {u'id': 1, u'name': u'folder2'},
                                    {u'id': 2, u'name': u'folder3'}]},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getMusicFolders'
        viewName = '%s.view' % methodName

        req = self._getRequest(viewName)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getNowPlaying(self):
        """
        since: 1.0.0

        Returns what is currently being played by all users

        Returns a dict like the following:

        {u'nowPlaying': {u'entry': {u'album': u"Jazz 'Round Midnight 12",
                            u'artist': u'Astrud Gilberto',
                            u'bitRate': 172,
                            u'contentType': u'audio/mpeg',
                            u'coverArt': u'98349284',
                            u'duration': 325,
                            u'genre': u'Jazz',
                            u'id': u'2424324',
                            u'isDir': False,
                            u'isVideo': False,
                            u'minutesAgo': 0,
                            u'parent': u'542352',
                            u'path': u"Astrud Gilberto/Jazz 'Round Midnight 12/01 - The Girl From Ipanema.mp3",
                            u'playerId': 1,
                            u'size': 7004089,
                            u'suffix': u'mp3',
                            u'title': u'The Girl From Ipanema',
                            u'track': 1,
                            u'username': u'user1',
                            u'year': 1996}},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getNowPlaying'
        viewName = '%s.view' % methodName

        req = self._getRequest(viewName)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getIndexes(self , musicFolderId=None , ifModifiedSince=0):
        """
        since: 1.0.0

        Returns an indexed structure of all artists

        musicFolderId:int       If this is specified, it will only return 
                                artists for the given folder ID from 
                                the getMusicFolders call
        ifModifiedSince:int     If specified, return a result if the artist
                                collection has changed since the given time

        Returns a dict like the following:

        {u'indexes': {u'index': [{u'artist': [{u'id': u'29834728934',
                                       u'name': u'A Perfect Circle'},
                                      {u'id': u'238472893',
                                       u'name': u'A Small Good Thing'},
                                      {u'id': u'9327842983',
                                       u'name': u'A Tribe Called Quest'},
                                      {u'id': u'29348729874',
                                       u'name': u'A-Teens, The'},
                                      {u'id': u'298472938',
                                       u'name': u'ABA STRUCTURE'}] ,
                      u'lastModified': 1303318347000L},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getIndexes'
        viewName = '%s.view' % methodName

        q = self._getQueryDict({'musicFolderId': musicFolderId , 
            'ifModifiedSince': self._ts2milli(ifModifiedSince)})

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getMusicDirectory(self , mid):
        """
        since: 1.0.0

        Returns a listing of all files in a music directory.  Typically used
        to get a list of albums for an artist or list of songs for an album.

        mid:str     The string ID value which uniquely identifies the 
                    folder.  Obtained via calls to getIndexes or 
                    getMusicDirectory.  REQUIRED

        Returns a dict like the following:

        {u'directory': {u'child': [{u'artist': u'A Tribe Called Quest',
                            u'coverArt': u'223484',
                            u'id': u'329084',
                            u'isDir': True,
                            u'parent': u'234823940',
                            u'title': u'Beats, Rhymes And Life'},
                           {u'artist': u'A Tribe Called Quest',
                            u'coverArt': u'234823794',
                            u'id': u'238472893',
                            u'isDir': True,
                            u'parent': u'2308472938',
                            u'title': u'Midnight Marauders'},
                           {u'artist': u'A Tribe Called Quest',
                            u'coverArt': u'39284792374',
                            u'id': u'983274892',
                            u'isDir': True,
                            u'parent': u'9823749',
                            u'title': u"People's Instinctive Travels And The Paths Of Rhythm"},
                           {u'artist': u'A Tribe Called Quest',
                            u'coverArt': u'289347293',
                            u'id': u'3894723934',
                            u'isDir': True,
                            u'parent': u'9832942',
                            u'title': u'The Anthology'},
                           {u'artist': u'A Tribe Called Quest',
                            u'coverArt': u'923847923',
                            u'id': u'29834729',
                            u'isDir': True,
                            u'parent': u'2934872893',
                            u'title': u'The Love Movement'},
                           {u'artist': u'A Tribe Called Quest',
                            u'coverArt': u'9238742893',
                            u'id': u'238947293',
                            u'isDir': True,
                            u'parent': u'9432878492',
                            u'title': u'The Low End Theory'}],
                u'id': u'329847293',
                u'name': u'A Tribe Called Quest'},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getMusicDirectory'
        viewName = '%s.view' % methodName

        req = self._getRequest(viewName , {'id': mid})
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def search(self , artist=None , album=None , title=None , any=None , 
            count=20 , offset=0 , newerThan=None):
        """
        since: 1.0.0

        DEPRECATED SINCE API 1.4.0!  USE search2() INSTEAD!

        Returns a listing of files matching the given search criteria.
        Supports paging with offset

        artist:str      Search for artist
        album:str       Search for album
        title:str       Search for title of song
        any:str         Search all fields
        count:int       Max number of results to return [default: 20]
        offset:int      Search result offset.  For paging [default: 0]
        newerThan:int   Return matches newer than this timestamp
        """
        if artist == album == title == any == None:
            raise ArgumentError('Invalid search.  You must supply search '
                'criteria')
        methodName = 'search'
        viewName = '%s.view' % methodName

        q = self._getQueryDict({'artist': artist , 'album': album , 
            'title': title , 'any': any , 'count': count , 'offset': offset ,
            'newerThan': self._ts2milli(newerThan)})

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def search2(self , query , artistCount=20 , artistOffset=0 , albumCount=20 ,
            albumOffset=0 , songCount=20 , songOffset=0):
        """
        since: 1.4.0

        Returns albums, artists and songs matching the given search criteria.
        Supports paging through the result.

        query:str           The search query
        artistCount:int     Max number of artists to return [default: 20]
        artistOffset:int    Search offset for artists (for paging) [default: 0]
        albumCount:int      Max number of albums to return [default: 20]
        albumOffset:int     Search offset for albums (for paging) [default: 0]
        songCount:int       Max number of songs to return [default: 20]
        songOffset:int      Search offset for songs (for paging) [default: 0]

        Returns a dict like the following:

        {u'searchResult2': {u'album': [{u'artist': u'A Tribe Called Quest',
                                u'coverArt': u'289347',
                                u'id': u'32487298',
                                u'isDir': True,
                                u'parent': u'98374289',
                                u'title': u'The Love Movement'}],
                    u'artist': [{u'id': u'2947839',
                                 u'name': u'A Tribe Called Quest'},
                                {u'id': u'239847239',
                                 u'name': u'Tribe'}],
                    u'song': [{u'album': u'Beats, Rhymes And Life',
                               u'artist': u'A Tribe Called Quest',
                               u'bitRate': 224,
                               u'contentType': u'audio/mpeg',
                               u'coverArt': u'329847',
                               u'duration': 148,
                               u'genre': u'default',
                               u'id': u'3928472893',
                               u'isDir': False,
                               u'isVideo': False,
                               u'parent': u'23984728394',
                               u'path': u'A Tribe Called Quest/Beats, Rhymes And Life/A Tribe Called Quest - Beats, Rhymes And Life - 03 - Motivators.mp3',
                               u'size': 4171913,
                               u'suffix': u'mp3',
                               u'title': u'Motivators',
                               u'track': 3}]},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'search2'
        viewName = '%s.view' % methodName

        q = {'query': query , 'artistCount': artistCount , 
            'artistOffset': artistOffset , 'albumCount': albumCount ,
            'albumOffset': albumOffset , 'songCount': songCount ,
            'songOffset': songOffset}

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def search3(self , query , artistCount=20 , artistOffset=0 , albumCount=20 ,
            albumOffset=0 , songCount=20 , songOffset=0):
        """
        since: 1.8.0

        Works the same way as search2, but uses ID3 tags for
        organization

        query:str           The search query
        artistCount:int     Max number of artists to return [default: 20]
        artistOffset:int    Search offset for artists (for paging) [default: 0]
        albumCount:int      Max number of albums to return [default: 20]
        albumOffset:int     Search offset for albums (for paging) [default: 0]
        songCount:int       Max number of songs to return [default: 20]
        songOffset:int      Search offset for songs (for paging) [default: 0]

        Returns a dict like the following (search for "Tune Yards":
            {u'searchResult3': {u'album': [{u'artist': u'Tune-Yards',
                                u'artistId': 1,
                                u'coverArt': u'al-7',
                                u'created': u'2012-01-30T12:35:33',
                                u'duration': 3229,
                                u'id': 7,
                                u'name': u'Bird-Brains',
                                u'songCount': 13},
                               {u'artist': u'Tune-Yards',
                                u'artistId': 1,
                                u'coverArt': u'al-8',
                                u'created': u'2011-03-22T15:08:00',
                                u'duration': 2531,
                                u'id': 8,
                                u'name': u'W H O K I L L',
                                u'songCount': 10}],
                    u'artist': {u'albumCount': 2,
                                u'coverArt': u'ar-1',
                                u'id': 1,
                                u'name': u'Tune-Yards'},
                    u'song': [{u'album': u'Bird-Brains',
                               u'albumId': 7,
                               u'artist': u'Tune-Yards',
                               u'artistId': 1,
                               u'bitRate': 160,
                               u'contentType': u'audio/mpeg',
                               u'coverArt': 105,
                               u'created': u'2012-01-30T12:35:33',
                               u'duration': 328,
                               u'genre': u'Lo-Fi',
                               u'id': 107,
                               u'isDir': False,
                               u'isVideo': False,
                               u'parent': 105,
                               u'path': u'Tune Yards/Bird-Brains/10-tune-yards-fiya.mp3',
                               u'size': 6588498,
                               u'suffix': u'mp3',
                               u'title': u'Fiya',
                               u'track': 10,
                               u'type': u'music',
                               u'year': 2009}]},

             u'status': u'ok',
             u'version': u'1.5.0',
             u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'search3'
        viewName = '%s.view' % methodName

        q = {'query': query , 'artistCount': artistCount , 
            'artistOffset': artistOffset , 'albumCount': albumCount ,
            'albumOffset': albumOffset , 'songCount': songCount ,
            'songOffset': songOffset}

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getPlaylists(self , username=None):
        """
        since: 1.0.0

        Returns the ID and name of all saved playlists
        The "username" option was added in 1.8.0.

        username:str        If specified, return playlists for this user
                            rather than for the authenticated user.  The
                            authenticated user must have admin role
                            if this parameter is used

        Returns a dict like the following:

        {u'playlists': {u'playlist': [{u'id': u'62656174732e6d3375',
                               u'name': u'beats'},
                              {u'id': u'766172696574792e6d3375',
                               u'name': u'variety'}]},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getPlaylists'
        viewName = '%s.view' % methodName

        q = self._getQueryDict({'username': username})

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getPlaylist(self , pid):
        """
        since: 1.0.0

        Returns a listing of files in a saved playlist

        id:str      The ID of the playlist as returned in getPlaylists()

        Returns a dict like the following:

        {u'playlist': {u'entry': {u'album': u'The Essential Bob Dylan',
                          u'artist': u'Bob Dylan',
                          u'bitRate': 32,
                          u'contentType': u'audio/mpeg',
                          u'coverArt': u'2983478293',
                          u'duration': 984,
                          u'genre': u'Classic Rock',
                          u'id': u'982739428',
                          u'isDir': False,
                          u'isVideo': False,
                          u'parent': u'98327428974',
                          u'path': u"Bob Dylan/Essential Bob Dylan Disc 1/Bob Dylan - The Essential Bob Dylan - 03 - The Times They Are A-Changin'.mp3",
                          u'size': 3921899,
                          u'suffix': u'mp3',
                          u'title': u"The Times They Are A-Changin'",
                          u'track': 3},
               u'id': u'44796c616e2e6d3375',
               u'name': u'Dylan'},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getPlaylist'
        viewName = '%s.view' % methodName

        req = self._getRequest(viewName , {'id': pid})
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def createPlaylist(self , playlistId=None , name=None , songIds=[]):
        """
        since: 1.2.0

        Creates OR updates a playlist.  If updating the list, the 
        playlistId is required.  If creating a list, the name is required.
        
        playlistId:str      The ID of the playlist to UPDATE
        name:str            The name of the playlist to CREATE
        songIds:list        The list of songIds to populate the list with in
                            either create or update mode.  Note that this
                            list will replace the existing list if updating

        Returns a dict like the following:

        {u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'createPlaylist'
        viewName = '%s.view' % methodName

        if playlistId == name == None:
            raise ArgumentError('You must supply either a playlistId or a name')
        if playlistId is not None and name is not None:
            raise ArgumentError('You can only supply either a playlistId '
                 'OR a name, not both')

        q = self._getQueryDict({'playlistId': playlistId , 'name': name})

        req = self._getRequestWithList(viewName , 'songId' , songIds , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def deletePlaylist(self , pid):
        """
        since: 1.2.0

        Deletes a saved playlist

        pid:str     ID of the playlist to delete, as obtained by getPlaylists

        Returns a dict like the following:

        """
        methodName = 'deletePlaylist'
        viewName = '%s.view' % methodName

        req = self._getRequest(viewName , {'id': pid})
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def download(self , sid):
        """
        since: 1.0.0

        Downloads a given music file.

        sid:str     The ID of the music file to download.

        Returns the file-like object for reading or raises an exception 
        on error
        """
        methodName = 'download'
        viewName = '%s.view' % methodName

        req = self._getRequest(viewName , {'id': sid})
        res = self._doBinReq(req)
        if isinstance(res , dict):
            self._checkStatus(res)
        return res

    def stream(self , sid , maxBitRate=0 , tformat=None , timeOffset=None ,
            size=None , estimateContentLength=False):
        """
        since: 1.0.0

        Downloads a given music file.

        sid:str         The ID of the music file to download.
        maxBitRate:int  (since: 1.2.0) If specified, the server will 
                        attempt to limit the bitrate to this value, in 
                        kilobits per second. If set to zero (default), no limit 
                        is imposed. Legal values are: 0, 32, 40, 48, 56, 64, 
                        80, 96, 112, 128, 160, 192, 224, 256 and 320.
        tformat:str     (since: 1.6.0) Specifies the target format
                        (e.g. "mp3" or "flv") in case there are multiple
                        applicable transcodings
        timeOffset:int  (since: 1.6.0) Only applicable to video 
                        streaming.  Start the stream at the given
                        offset (in seconds) into the video
        size:str        (since: 1.6.0) The requested video size in
                        WxH, for instance 640x480
        estimateContentLength:bool  (since: 1.8.0) If set to True,
                                    the HTTP Content-Length header
                                    will be set to an estimated
                                    value for trancoded media

        Returns the file-like object for reading or raises an exception 
        on error
        """
        methodName = 'stream'
        viewName = '%s.view' % methodName
        
        q = self._getQueryDict({'id': sid , 'maxBitRate': maxBitRate ,
            'format': tformat , 'timeOffset': timeOffset , 'size': size ,
            'estimateContentLength': estimateContentLength})

        req = self._getRequest(viewName , q)
        res = self._doBinReq(req)
        if isinstance(res , dict):
            self._checkStatus(res)
        return res

    def getCoverArt(self , aid , size=None):
        """
        since: 1.0.0

        Returns a cover art image

        aid:str     ID string for the cover art image to download
        size:int    If specified, scale image to this size

        Returns the file-like object for reading or raises an exception 
        on error
        """
        methodName = 'getCoverArt'
        viewName = '%s.view' % methodName
        
        q = self._getQueryDict({'id': aid , 'size': size})

        req = self._getRequest(viewName , q)
        res = self._doBinReq(req)
        if isinstance(res , dict):
            self._checkStatus(res)
        return res

    def scrobble(self , sid , submission=True):
        """
        since: 1.5.0

        "Scrobbles" a given music file on last.fm.  Requires that the user
        has set this up.

        sid:str             The ID of the file to scrobble
        submission:bool     Whether this is a "submission" or a "now playing"
                            notification

        Returns a dict like the following:

        {u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'scrobble'
        viewName = '%s.view' % methodName

        q = {'id': sid , 'submission': submission}

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def changePassword(self , username , password):
        """
        since: 1.1.0

        Changes the password of an existing Subsonic user.  Note that the
        user performing this must have admin privileges

        username:str        The username whose password is being changed
        password:str        The new password of the user

        Returns a dict like the following:

        {u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'changePassword'
        viewName = '%s.view' % methodName
        hexPass = 'enc:%s' % self._hexEnc(password)

        # There seems to be an issue with some subsonic implementations
        # not recognizing the "enc:" precursor to the encoded password and 
        # encodes the whole "enc:<hex>" as the password.  Weird.
        #q = {'username': username , 'password': hexPass.lower()}
        q = {'username': username , 'password': password}

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getUser(self , username):
        """
        since: 1.3.0

        Get details about a given user, including which auth roles it has.
        Can be used to enable/disable certain features in the client, such
        as jukebox control

        username:str        The username to retrieve.  You can only retrieve 
                            your own user unless you have admin privs.

        Returns a dict like the following:

        {u'status': u'ok', 
         u'user': {u'adminRole': False,
               u'commentRole': False,
               u'coverArtRole': False,
               u'downloadRole': True,
               u'jukeboxRole': False,
               u'playlistRole': True,
               u'podcastRole': False,
               u'settingsRole': True,
               u'streamRole': True,
               u'uploadRole': True,
               u'username': u'test'},
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getUser'
        viewName = '%s.view' % methodName

        q = {'username': username}

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def createUser(self , username , password , ldapAuthenticated=False ,
            adminRole=False , settingsRole=True , streamRole=True ,
            jukeboxRole=False , downloadRole=False , uploadRole=False ,
            playlistRole=False , coverArtRole=False , commentRole=False ,
            podcastRole=False , shareRole=False):
        """
        since: 1.1.0

        Creates a new subsonic user, using the parameters defined.  See the
        documentation at http://subsonic.org for more info on all the roles.

        username:str        The username of the new user
        password:str        The password for the new user
        <For info on the boolean roles, see http://subsonic.org for more info>

        Returns a dict like the following:

        {u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'createUser'
        viewName = '%s.view' % methodName
        hexPass = 'enc:%s' % self._hexEnc(password)

        q = {'username': username , 'password': hexPass ,
            'ldapAuthenticated': ldapAuthenticated , 'adminRole': adminRole ,
            'settingsRole': settingsRole , 'streamRole': streamRole ,
            'jukeboxRole': jukeboxRole , 'downloadRole': downloadRole ,
            'uploadRole': uploadRole , 'playlistRole': playlistRole ,
            'coverArtRole': coverArtRole , 'commentRole': commentRole ,
            'podcastRole': podcastRole , 'shareRole': shareRole}

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def deleteUser(self , username):
        """
        since: 1.3.0

        Deletes an existing Subsonic user.  Of course, you must have admin
        rights for this.

        username:str        The username of the user to delete

        Returns a dict like the following:

        {u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'deleteUser'
        viewName = '%s.view' % methodName

        q = {'username': username}

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res
    
    def getChatMessages(self , since=1):
        """
        since: 1.2.0

        Returns the current visible (non-expired) chat messages.

        since:int       Only return messages newer than this timestamp

        NOTE: All times returned are in MILLISECONDS since the Epoch, not
              seconds!

        Returns a dict like the following:
        {u'chatMessages': {u'chatMessage': {u'message': u'testing 123',
                                            u'time': 1303411919872L,
                                            u'username': u'admin'}},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getChatMessages'
        viewName = '%s.view' % methodName

        q = {'since': self._ts2milli(since)}

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def addChatMessage(self , message):
        """
        since: 1.2.0

        Adds a message to the chat log

        message:str     The message to add

        Returns a dict like the following:

        {u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'addChatMessage'
        viewName = '%s.view' % methodName

        q = {'message': message}

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getAlbumList(self , ltype , size=10 , offset=0):
        """
        since: 1.2.0

        Returns a list of random, newest, highest rated etc. albums. 
        Similar to the album lists on the home page of the Subsonic 
        web interface

        ltype:str       The list type. Must be one of the following: random, 
                        newest, highest, frequent, recent, 
                        (since 1.8.0 -> )starred, alphabeticalByName, 
                        alphabeticalByArtist
        size:int        The number of albums to return. Max 500
        offset:int      The list offset. Use for paging. Max 5000

        Returns a dict like the following:

        {u'albumList': {u'album': [{u'artist': u'Hank Williams',
                            u'id': u'3264928374',
                            u'isDir': True,
                            u'parent': u'9238479283',
                            u'title': u'The Original Singles Collection...Plus'},
                           {u'artist': u'Freundeskreis',
                            u'coverArt': u'9823749823',
                            u'id': u'23492834',
                            u'isDir': True,
                            u'parent': u'9827492374',
                            u'title': u'Quadratur des Kreises'}]},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getAlbumList'
        viewName = '%s.view' % methodName

        q = {'type': ltype , 'size': size , 'offset': offset}

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getAlbumList2(self , ltype , size=10 , offset=0):
        """
        since 1.8.0

        Returns a list of random, newest, highest rated etc. albums. 
        This is similar to getAlbumList, but uses ID3 tags for
        organization

        ltype:str       The list type. Must be one of the following: random, 
                        newest, highest, frequent, recent, 
                        (since 1.8.0 -> )starred, alphabeticalByName, 
                        alphabeticalByArtist
        size:int        The number of albums to return. Max 500
        offset:int      The list offset. Use for paging. Max 5000

        Returns a dict like the following:
           {u'albumList2': {u'album': [{u'artist': u'Massive Attack',
                             u'artistId': 0,
                             u'coverArt': u'al-0',
                             u'created': u'2009-08-28T10:00:44',
                             u'duration': 3762,
                             u'id': 0,
                             u'name': u'100th Window',
                             u'songCount': 9},
                            {u'artist': u'Massive Attack',
                             u'artistId': 0,
                             u'coverArt': u'al-5',
                             u'created': u'2003-11-03T22:00:00',
                             u'duration': 2715,
                             u'id': 5,
                             u'name': u'Blue Lines',
                             u'songCount': 9}]},
            u'status': u'ok',
            u'version': u'1.8.0',
            u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getAlbumList2'
        viewName = '%s.view' % methodName

        q = {'type': ltype , 'size': size , 'offset': offset}

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getRandomSongs(self , size=10 , genre=None , fromYear=None , 
            toYear=None , musicFolderId=None):
        """
        since 1.2.0

        Returns random songs matching the given criteria

        size:int            The max number of songs to return. Max 500
        genre:str           Only return songs from this genre
        fromYear:int        Only return songs after or in this year
        toYear:int          Only return songs before or in this year
        musicFolderId:str   Only return songs in the music folder with the
                            given ID.  See getMusicFolders

        Returns a dict like the following:

        {u'randomSongs': {u'song': [{u'album': u'1998 EP - Airbag (How Am I Driving)',
                             u'artist': u'Radiohead',
                             u'bitRate': 320,
                             u'contentType': u'audio/mpeg',
                             u'duration': 129,
                             u'id': u'9284728934',
                             u'isDir': False,
                             u'isVideo': False,
                             u'parent': u'983249823',
                             u'path': u'Radiohead/1998 EP - Airbag (How Am I Driving)/06 - Melatonin.mp3',
                             u'size': 5177469,
                             u'suffix': u'mp3',
                             u'title': u'Melatonin'},
                            {u'album': u'Mezmerize',
                             u'artist': u'System Of A Down',
                             u'bitRate': 214,
                             u'contentType': u'audio/mpeg',
                             u'coverArt': u'23849372894',
                             u'duration': 176,
                             u'id': u'28937492834',
                             u'isDir': False,
                             u'isVideo': False,
                             u'parent': u'92837492837',
                             u'path': u'System Of A Down/Mesmerize/10 - System Of A Down - Old School Hollywood.mp3',
                             u'size': 4751360,
                             u'suffix': u'mp3',
                             u'title': u'Old School Hollywood',
                             u'track': 10}]},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getRandomSongs'
        viewName = '%s.view' % methodName

        q = self._getQueryDict({'size': size , 'genre': genre , 
            'fromYear': fromYear , 'toYear': toYear , 
            'musicFolderId': musicFolderId})

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getLyrics(self , artist=None , title=None):
        """
        since: 1.2.0

        Searches for and returns lyrics for a given song

        artist:str      The artist name
        title:str       The song title

        Returns a dict like the following for 
        getLyrics('Bob Dylan' , 'Blowin in the wind'):

        {u'lyrics': {u'artist': u'Bob Dylan',
             u'content': u"How many roads must a man walk down<snip>",
             u'title': u"Blowin' in the Wind"},
         u'status': u'ok',
         u'version': u'1.5.0',
         u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getLyrics'
        viewName = '%s.view' % methodName

        q = self._getQueryDict({'artist': artist , 'title': title})

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def jukeboxControl(self , action , index=None , sids=[] , gain=None , 
            offset=None):
        """
        since: 1.2.0

        NOTE: Some options were added as of API version 1.7.0

        Controls the jukebox, i.e., playback directly on the server's 
        audio hardware. Note: The user must be authorized to control 
        the jukebox

        action:str      The operation to perform. Must be one of: get, 
                        start, stop, skip, add, clear, remove, shuffle, 
                        setGain, status (added in API 1.7.0), 
                        set (added in API 1.7.0)
        index:int       Used by skip and remove. Zero-based index of the 
                        song to skip to or remove.
        sids:str        Used by "add" and "set". ID of song to add to the 
                        jukebox playlist. Use multiple id parameters to 
                        add many songs in the same request.  Whether you 
                        are passing one song or many into this, this 
                        parameter MUST be a list
        gain:float      Used by setGain to control the playback volume. 
                        A float value between 0.0 and 1.0
        offset:int      (added in API 1.7.0) Used by "skip".  Start playing
                        this many seconds into the track.
        """
        methodName = 'jukeboxControl'
        viewName = '%s.view' % methodName

        q = self._getQueryDict({'action': action , 'index': index , 
            'gain': gain , 'offset': offset})

        req = None
        if action == 'add':
            # We have to deal with the sids
            if not (isinstance(sids , list) or isinstance(sids , tuple)):
                raise ArgumentError('If you are adding songs, "sids" must '
                    'be a list or tuple!')
            req = self._getRequestWithList(viewName , 'id' , sids , q)
        else:
            req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getPodcasts(self):
        """
        since: 1.6.0

        Returns all podcast channels the server subscribes to and their 
        episodes.

        Returns a dict like the following:
        {u'status': u'ok',
         u'version': u'1.6.0',
         u'xmlns': u'http://subsonic.org/restapi',
         u'podcasts': {u'channel': {u'description': u"Dr Chris Smith...",
                            u'episode': [{u'album': u'Dr Karl and the Naked Scientist',
                                          u'artist': u'BBC Radio 5 live',
                                          u'bitRate': 64,
                                          u'contentType': u'audio/mpeg',
                                          u'coverArt': u'2f6f7074',
                                          u'description': u'Dr Karl answers all your science related questions.',
                                          u'duration': 2902,
                                          u'genre': u'Podcast',
                                          u'id': 0,
                                          u'isDir': False,
                                          u'isVideo': False,
                                          u'parent': u'2f6f70742f737562736f6e69632f706f6463617374732f4472204b61726c20616e6420746865204e616b656420536369656e74697374',
                                          u'publishDate': u'2011-08-17 22:06:00.0',
                                          u'size': 23313059,
                                          u'status': u'completed',
                                          u'streamId': u'2f6f70742f737562736f6e69632f706f6463617374732f4472204b61726c20616e6420746865204e616b656420536369656e746973742f64726b61726c5f32303131303831382d30343036612e6d7033',
                                          u'suffix': u'mp3',
                                          u'title': u'DrKarl: Peppermints, Chillies & Receptors',
                                          u'year': 2011},
                                         {u'description': u'which is warmer, a bath with bubbles in it or one without?  Just one of the stranger science stories tackled this week by Dr Chris Smith and the Naked Scientists!',
                                          u'id': 1,
                                          u'publishDate': u'2011-08-14 21:05:00.0',
                                          u'status': u'skipped',
                                          u'title': u'DrKarl: how many bubbles in your bath? 15 AUG 11'},
                                          ...
                                         {u'description': u'Dr Karl joins Rhod to answer all your science questions',
                                          u'id': 9,
                                          u'publishDate': u'2011-07-06 22:12:00.0',
                                          u'status': u'skipped',
                                          u'title': u'DrKarl: 8 Jul 11 The Strange Sound of the MRI Scanner'}],
                            u'id': 0,
                            u'status': u'completed',
                            u'title': u'Dr Karl and the Naked Scientist',
                            u'url': u'http://downloads.bbc.co.uk/podcasts/fivelive/drkarl/rss.xml'}}
        }

        See also: http://subsonic.svn.sourceforge.net/viewvc/subsonic/trunk/subsonic-main/src/main/webapp/xsd/podcasts_example_1.xml?view=markup
        """
        methodName = 'getPodcasts'
        viewName = '%s.view' % methodName

        req = self._getRequest(viewName)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getShares(self):
        """
        since: 1.6.0

        Returns information about shared media this user is allowed to manage

        Note that entry can be either a single dict or a list of dicts

        Returns a dict like the following:

        {u'status': u'ok',
         u'version': u'1.6.0',
         u'xmlns': u'http://subsonic.org/restapi',
         u'shares': {u'share': [
             {u'created': u'2011-08-18T10:01:35',
              u'entry': {u'artist': u'Alice In Chains',
                         u'coverArt': u'2f66696c65732f6d7033732f412d4d2f416c69636520496e20436861696e732f416c69636520496e20436861696e732f636f7665722e6a7067',
                         u'id': u'2f66696c65732f6d7033732f412d4d2f416c69636520496e20436861696e732f416c69636520496e20436861696e73',
                         u'isDir': True,
                         u'parent': u'2f66696c65732f6d7033732f412d4d2f416c69636520496e20436861696e73',
                         u'title': u'Alice In Chains'},
              u'expires': u'2012-08-18T10:01:35',
              u'id': 0,
              u'url': u'http://crustymonkey.subsonic.org/share/BuLbF',
              u'username': u'admin',
              u'visitCount': 0
             }]}
        }
        """
        methodName = 'getShares'
        viewName = '%s.view' % methodName

        req = self._getRequest(viewName)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def createShare(self , shids=[] , description=None , expires=None):
        """
        since: 1.6.0

        Creates a public URL that can be used by anyone to stream music 
        or video from the Subsonic server. The URL is short and suitable 
        for posting on Facebook, Twitter etc. Note: The user must be 
        authorized to share (see Settings > Users > User is allowed to 
        share files with anyone).

        shids:list[str]              A list of ids of songs, albums or videos 
                                    to share.
        description:str             A description that will be displayed to
                                    people visiting the shared media 
                                    (optional).
        expires:float               A timestamp pertaining to the time at
                                    which this should expire (optional)

        This returns a structure like you would get back from getShares()
        containing just your new share.
        """
        methodName = 'createShare'
        viewName = '%s.view' % methodName

        q = self._getQueryDict({'description': description , 
            'expires': self._ts2milli(expires)})
        req = self._getRequestWithList(viewName , 'id' , shids , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def updateShare(self , shid , description=None , expires=None):
        """
        since: 1.6.0

        Updates the description and/or expiration date for an existing share

        shid:str            The id of the share to update
        description:str     The new description for the share (optional).
        expires:float       The new timestamp for the expiration time of this
                            share (optional).
        """
        methodName = 'updateShare'
        viewName = '%s.view' % methodName

        q = self._getQueryDict({'id': shid , 'description': description ,
            expires: self._ts2milli(expires)})

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def deleteShare(self , shid):
        """
        since: 1.6.0

        Deletes an existing share

        shid:str        The id of the share to delete

        Returns a standard response dict
        """
        methodName = 'deleteShare'
        viewName = '%s.view' % methodName

        q = self._getQueryDict({'id': shid})

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def setRating(self , id , rating):
        """
        since: 1.6.0

        Sets the rating for a music file

        id:str          The id of the item (song/artist/album) to rate
        rating:int      The rating between 1 and 5 (inclusive), or 0 to remove
                        the rating

        Returns a standard response dict
        """
        methodName = 'setRating'
        viewName = '%s.view' % methodName

        try:
            rating = int(rating)
        except:
            raise ArgumentError('Rating must be an integer between 0 and 5: '
                '%r' % rating)
        if rating < 0 or rating > 5:
            raise ArgumentError('Rating must be an integer between 0 and 5: '
                '%r' % rating)

        q = self._getQueryDict({'id': id , 'rating': rating})
        
        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getArtists(self):
        """
        since 1.8.0

        Similar to getIndexes(), but this method uses the ID3 tags to
        determine the artist

        Returns a dict like the following:
            {u'artists': {u'index': [{u'artist': {u'albumCount': 7,
                                      u'coverArt': u'ar-0',
                                      u'id': 0,
                                      u'name': u'Massive Attack'},
                          u'name': u'M'},
                         {u'artist': {u'albumCount': 2,
                                      u'coverArt': u'ar-1',
                                      u'id': 1,
                                      u'name': u'Tune-Yards'},
                          u'name': u'T'}]},
             u'status': u'ok',
             u'version': u'1.8.0',
             u'xmlns': u'http://subsonic.org/restapi'}    
        """
        methodName = 'getArtists'
        viewName = '%s.view' % methodName
        
        req = self._getRequest(viewName)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getArtist(self , id):
        """
        since 1.8.0

        Returns the info (albums) for an artist.  This method uses 
        the ID3 tags for organization

        id:str      The artist ID

        Returns a dict like the following:
            
           {u'artist': {u'album': [{u'artist': u'Tune-Yards',
                         u'artistId': 1,
                         u'coverArt': u'al-7',
                         u'created': u'2012-01-30T12:35:33',
                         u'duration': 3229,
                         u'id': 7,
                         u'name': u'Bird-Brains',
                         u'songCount': 13},
                        {u'artist': u'Tune-Yards',
                         u'artistId': 1,
                         u'coverArt': u'al-8',
                         u'created': u'2011-03-22T15:08:00',
                         u'duration': 2531,
                         u'id': 8,
                         u'name': u'W H O K I L L',
                         u'songCount': 10}],
             u'albumCount': 2,
             u'coverArt': u'ar-1',
             u'id': 1,
             u'name': u'Tune-Yards'},
            u'status': u'ok',
            u'version': u'1.8.0',
            u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getArtist'
        viewName = '%s.view' % methodName

        q = self._getQueryDict({'id': id})

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getAlbum(self , id):
        """
        since 1.8.0

        Returns the info and songs for an album.  This method uses
        the ID3 tags for organization

        id:str      The album ID

        Returns a dict like the following:
            
           {u'album': {u'artist': u'Massive Attack',
            u'artistId': 0,
            u'coverArt': u'al-0',
            u'created': u'2009-08-28T10:00:44',
            u'duration': 3762,
            u'id': 0,
            u'name': u'100th Window',
            u'song': [{u'album': u'100th Window',
                       u'albumId': 0,
                       u'artist': u'Massive Attack',
                       u'artistId': 0,
                       u'bitRate': 192,
                       u'contentType': u'audio/mpeg',
                       u'coverArt': 2,
                       u'created': u'2009-08-28T10:00:57',
                       u'duration': 341,
                       u'genre': u'Rock',
                       u'id': 14,
                       u'isDir': False,
                       u'isVideo': False,
                       u'parent': 2,
                       u'path': u'Massive Attack/100th Window/01 - Future Proof.mp3',
                       u'size': 8184445,
                       u'suffix': u'mp3',
                       u'title': u'Future Proof',
                       u'track': 1,
                       u'type': u'music',
                       u'year': 2003}],
              u'songCount': 9},
            u'status': u'ok',
            u'version': u'1.8.0',
            u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getAlbum'
        viewName = '%s.view' % methodName

        q = self._getQueryDict({'id': id})

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getSong(self , id):
        """
        since 1.8.0

        Returns the info for a song.  This method uses the ID3 
        tags for organization

        id:str      The song ID

        Returns a dict like the following:
            {u'song': {u'album': u'W H O K I L L',
               u'albumId': 8,
               u'artist': u'Tune-Yards',
               u'artistId': 1,
               u'bitRate': 320,
               u'contentType': u'audio/mpeg',
               u'coverArt': 106,
               u'created': u'2011-03-22T15:08:00',
               u'discNumber': 1,
               u'duration': 192,
               u'genre': u'Indie Rock',
               u'id': 120,
               u'isDir': False,
               u'isVideo': False,
               u'parent': 106,
               u'path': u'Tune Yards/Who Kill/10 Killa.mp3',
               u'size': 7692656,
               u'suffix': u'mp3',
               u'title': u'Killa',
               u'track': 10,
               u'type': u'music',
               u'year': 2011},
             u'status': u'ok',
             u'version': u'1.8.0',
             u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getSong'
        viewName = '%s.view' % methodName

        q = self._getQueryDict({'id': id})

        req = self._getRequest(viewName , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getVideos(self):
        """
        since 1.8.0

        Returns all video files

        Returns a dict like the following:
            {u'status': u'ok',
             u'version': u'1.8.0',
             u'videos': {u'video': {u'bitRate': 384,
                        u'contentType': u'video/x-matroska',
                        u'created': u'2012-08-26T13:36:44',
                        u'duration': 1301,
                        u'id': 130,
                        u'isDir': False,
                        u'isVideo': True,
                        u'path': u'South Park - 16x07 - Cartman Finds Love.mkv',
                        u'size': 287309613,
                        u'suffix': u'mkv',
                        u'title': u'South Park - 16x07 - Cartman Finds Love',
                        u'transcodedContentType': u'video/x-flv',
                        u'transcodedSuffix': u'flv'}},
             u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getVideos'
        viewName = '%s.view' % methodName

        req = self._getRequest(viewName)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getStarred(self):
        """
        since 1.8.0

        Returns starred songs, albums and artists

        Returns a dict like the following:
            {u'starred': {u'album': {u'album': u'Bird-Brains',
                         u'artist': u'Tune-Yards',
                         u'coverArt': 105,
                         u'created': u'2012-01-30T13:16:58',
                         u'id': 105,
                         u'isDir': True,
                         u'parent': 104,
                         u'starred': u'2012-08-26T13:18:34',
                         u'title': u'Bird-Brains'},
              u'song': [{u'album': u'Mezzanine',
                         u'albumId': 4,
                         u'artist': u'Massive Attack',
                         u'artistId': 0,
                         u'bitRate': 256,
                         u'contentType': u'audio/mpeg',
                         u'coverArt': 6,
                         u'created': u'2009-06-15T07:48:28',
                         u'duration': 298,
                         u'genre': u'Dub',
                         u'id': 72,
                         u'isDir': False,
                         u'isVideo': False,
                         u'parent': 6,
                         u'path': u'Massive Attack/Mezzanine/Massive Attack_02_mezzanine.mp3',
                         u'size': 9564160,
                         u'starred': u'2012-08-26T13:19:26',
                         u'suffix': u'mp3',
                         u'title': u'Risingson',
                         u'track': 2,
                         u'type': u'music'},
                        {u'album': u'Mezzanine',
                         u'albumId': 4,
                         u'artist': u'Massive Attack',
                         u'artistId': 0,
                         u'bitRate': 256,
                         u'contentType': u'audio/mpeg',
                         u'coverArt': 6,
                         u'created': u'2009-06-15T07:48:25',
                         u'duration': 380,
                         u'genre': u'Dub',
                         u'id': 71,
                         u'isDir': False,
                         u'isVideo': False,
                         u'parent': 6,
                         u'path': u'Massive Attack/Mezzanine/Massive Attack_01_mezzanine.mp3',
                         u'size': 12179456,
                         u'starred': u'2012-08-26T13:19:03',
                         u'suffix': u'mp3',
                         u'title': u'Angel',
                         u'track': 1,
                         u'type': u'music'}]},
             u'status': u'ok',
             u'version': u'1.8.0',
             u'xmlns': u'http://subsonic.org/restapi'}
        """
        methodName = 'getStarred'
        viewName = '%s.view' % methodName

        req = self._getRequest(viewName)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getStarred2(self):
        """
        since 1.8.0

        Returns starred songs, albums and artists like getStarred(),
        but this uses ID3 tags for organization

        Returns a dict like the following:
            
            **See the output from getStarred()**
        """
        methodName = 'getStarred2'
        viewName = '%s.view' % methodName

        req = self._getRequest(viewName)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def updatePlaylist(self , lid , name=None , comment=None , songIdsToAdd=[] ,
            songIndexesToRemove=[]):
        """
        since 1.8.0

        Updates a playlist.  Only the owner of a playlist is allowed to
        update it.

        lid:str                 The playlist id
        name:str                The human readable name of the playlist
        comment:str             The playlist comment
        songIdsToAdd:list       A list of song IDs to add to the playlist
        songIndexesToRemove:list    Remove the songs at the 
                                    0 BASED INDEXED POSITIONS in the
                                    playlist, NOT the song ids.  Note that 
                                    this is always a list.
        
        Returns a normal status response dict
        """
        methodName = 'updatePlaylist'
        viewName = '%s.view' % methodName

        q = self._getQueryDict({'playlistId': lid , 'name': name ,
            'comment': comment})
        if not isinstance(songIdsToAdd , list) or isinstance(songIdsToAdd ,
                tuple):
            songIdsToAdd = [songIdsToAdd]
        if not isinstance(songIndexesToRemove , list) or isinstance(
                songIndexesToRemove , tuple):
            songIndexesToRemove = [songIndexesToRemove]
        listMap = {'songIdToAdd': songIdsToAdd ,
            'songIndexToRemove': songIndexesToRemove}
        req = self._getRequestWithLists(viewName , listMap , q)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def getAvatar(self , username):
        """
        since 1.8.0

        Returns the avatar for a user or None if the avatar does not exist

        username:str    The user to retrieve the avatar for

        Returns the file-like object for reading or raises an exception 
        on error
        """
        methodName = 'getAvatar'
        viewName = '%s.view' % methodName
        
        q = {'username': username}

        req = self._getRequest(viewName , q)
        try:
            res = self._doBinReq(req)
        except urllib2.HTTPError:
            # Avatar is not set/does not exist, return None
            return None
        if isinstance(res , dict):
            self._checkStatus(res)
        return res

    def star(self , sids=[] , albumIds=[] , artistIds=[]):
        """
        since 1.8.0

        Attaches a star to songs, albums or artists

        sids:list       A list of song IDs to star
        albumIds:list   A list of album IDs to star.  Use this rather than
                        "sids" if the client access the media collection
                        according to ID3 tags rather than file
                        structure
        artistIds:list  The ID of an artist to star.  Use this rather
                        than sids if the client access the media
                        collection according to ID3 tags rather
                        than file structure

        Returns a normal status response dict
        """
        methodName = 'star'
        viewName = '%s.view' % methodName

        if not isinstance(sids , list) or isinstance(sids , tuple):
            sids = [sids]
        if not isinstance(albumIds , list) or isinstance(albumIds , tuple):
            albumIds = [albumIds]
        if not isinstance(artistIds , list) or isinstance(artistIds , tuple):
            artistIds = [artistIds]
        listMap = {'id': sids ,
            'albumId': albumIds ,
            'artistId': artistIds}
        req = self._getRequestWithLists(viewName , listMap)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    def unstar(self , sids=[] , albumIds=[] , artistIds=[]):
        """
        since 1.8.0

        Removes a star to songs, albums or artists.  Basically, the
        same as star in reverse

        sids:list       A list of song IDs to star
        albumIds:list   A list of album IDs to star.  Use this rather than
                        "sids" if the client access the media collection
                        according to ID3 tags rather than file
                        structure
        artistIds:list  The ID of an artist to star.  Use this rather
                        than sids if the client access the media
                        collection according to ID3 tags rather
                        than file structure

        Returns a normal status response dict
        """
        methodName = 'unstar'
        viewName = '%s.view' % methodName

        if not isinstance(sids , list) or isinstance(sids , tuple):
            sids = [sids]
        if not isinstance(albumIds , list) or isinstance(albumIds , tuple):
            albumIds = [albumIds]
        if not isinstance(artistIds , list) or isinstance(artistIds , tuple):
            artistIds = [artistIds]
        listMap = {'id': sids ,
            'albumId': albumIds ,
            'artistId': artistIds}
        req = self._getRequestWithLists(viewName , listMap)
        res = self._doInfoReq(req)
        self._checkStatus(res)
        return res

    # Private internal methods
    def _getOpener(self , username , passwd):
        creds = b64encode('%s:%s' % (username , passwd))
        opener = urllib2.build_opener(PysHTTPRedirectHandler , 
           HTTPSHandlerV3)
        opener.addheaders = [('Authorization' , 'Basic %s' % creds)]
        return opener

    def _getQueryDict(self , d):
        """
        Given a dictionary, it cleans out all the values set to None
        """
        for k , v in d.items():
            if v is None:
                del d[k]
        return d

    def _getRequest(self , viewName , query={}):
        qstring = {'f': 'json' , 'v': self._apiVersion , 'c': self._appName}
        qstring.update(query)
        url = '%s:%d/%s/%s' % (self._baseUrl , self._port , self._serverPath ,
            viewName)
        req = urllib2.Request(url , urlencode(qstring))
        return req

    def _getRequestWithList(self , viewName , listName , alist , query={}):
        """
        Like _getRequest, but allows appending a number of items with the
        same key (listName).  This bypasses the limitation of urlencode()
        """
        qstring = {'f': 'json' , 'v': self._apiVersion , 'c': self._appName}
        qstring.update(query)
        url = '%s:%d/%s/%s' % (self._baseUrl , self._port , self._serverPath ,
            viewName)
        data = StringIO()
        data.write(urlencode(qstring))
        for i in alist:
            data.write('&%s' % urlencode({listName: i}))
        req = urllib2.Request(url , data.getvalue())
        return req

    def _getRequestWithLists(self , viewName , listMap , query={}):
        """
        Like _getRequestWithList(), but you must pass a dictionary 
        that maps the listName to the list.  This allows for multiple 
        list parameters to be used, like in updatePlaylist()

        viewName:str        The name of the view
        listMap:dict        A mapping of listName to a list of entries
        query:dict          The normal query dict
        """
        qstring = {'f': 'json' , 'v': self._apiVersion , 'c': self._appName}
        qstring.update(query)
        url = '%s:%d/%s/%s' % (self._baseUrl , self._port , self._serverPath ,
            viewName)
        data = StringIO()
        data.write(urlencode(qstring))
        for k , l in listMap.iteritems():
            for i in l:
                data.write('&%s' % urlencode({k: i}))
        req = urllib2.Request(url , data.getvalue())
        return req

    def _doInfoReq(self , req):
        # Returns a parsed dictionary version of the result
        res = self._opener.open(req)
        dres = json.loads(res.read())
        return dres['subsonic-response']

    def _doBinReq(self , req):
        res = self._opener.open(req)
        contType = res.info().getheader('Content-Type')
        if contType:
            if contType.startswith('text/html') or \
                    contType.startswith('application/json'):
                dres = json.loads(res.read())
                return dres['subsonic-response']
        return res

    def _checkStatus(self , result):
        if result['status'] == 'ok':
            return True
        elif result['status'] == 'failed':
            exc = getExcByCode(result['error']['code'])
            raise exc(result['error']['message'])

    def _hexEnc(self , raw):
        """
        Returns a "hex encoded" string per the Subsonic api docs

        raw:str     The string to hex encode
        """
        ret = ''
        for c in raw:
            ret += '%02X' % ord(c)
        return ret

    def _ts2milli(self , ts):
        """
        For whatever reason, Subsonic uses timestamps in milliseconds since
        the unix epoch.  I have no idea what need there is of this precision,
        but this will just multiply the timestamp times 1000 and return the int
        """
        if ts is None:
            return None
        return int(ts * 1000)
