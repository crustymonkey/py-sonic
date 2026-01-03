"""
This file is part of py-opensonic.

py-opensonic is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

py-opensonic is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with py-opensonic.  If not, see <http://www.gnu.org/licenses/>
"""

from netrc import netrc
from hashlib import md5
import os

import aiohttp
from aiohttp import ClientResponse, ClientTimeout

from .conn_base import ConnBase, API_VERSION
from . import errors
from .media.media_types import (Album, AlbumID3, AlbumInfo, ArtistID3, ArtistInfo, ArtistInfo2,
                                Artists, Bookmark, ChatMessage, Child, Directory, Error, Genre,
                                Indexes, InternetRadioStation, JukeboxPlaylist, JukeboxStatus,
                                Lyrics, MusicFolder, NowPlayingEntry, OpenSubsonicExtension,
                                Playlist, PlayQueue, PodcastChannel, PodcastEpisode, ScanStatus,
                                SearchResult2, SearchResult3, Share, Starred, Starred2,
                                StructuredLyrics, User)


class AsyncConnection(ConnBase[ClientResponse]):
    """
    This is the only class used to make calls of an OpenSubsonic server. All return types are
    defined in media.media_types.py.
    """
    def __init__(self, base_url:str, username:str, password:str, port:int=4040,
                 api_key:str|None=None, server_path:str='', app_name:str='py-opensonic', api_version:str=API_VERSION,
                 use_netrc:str|None=None, legacy_auth:bool=False,
                 use_get:bool=False, use_views:bool=True):
        """
        This will create a connection to your subsonic server

        base_url:str         The base url for your server. Be sure to use
                            "https" for SSL connections.  If you are using
                            a port other than the default 4040, be sure to
                            specify that with the port argument.  Do *not*
                            append it here.

                            ex: http://subsonic.example.com

                            If you are running subsonic under a different
                            path, specify that with the "server_path" arg,
                            *not* here.  For example, if your subsonic
                            lives at:

                            https://mydomain.com:8080/path/to/subsonic/rest

                            You would set the following:

                            base_url = "https://mydomain.com"
                            port = 8080
                            server_path = "/path/to/subsonic/rest"
        username:str        The username to use for the connection.  This
                            can be None if you are using api key authentication or `use_netrc' is True (and you
                            have a valid entry in your netrc file)
        password:str        The password to use for the connection.  This
                            can be None if you are using api key authentication or `use_netrc' is True (and you
                            have a valid entry in your netrc file)
        port:int            The port number to connect on.  The default for
                            unencrypted subsonic connections is 4040
        api_key:str         API key used for authentication as defined by Open Subsonic's API key extension.
        server_path:str      The base resource path for the subsonic views.
                            This is useful if you have your subsonic server
                            behind a proxy and the path that you are proxying
                            is different from the default of '/rest'.
                            Ex:
                                server_path='/path/to/subs'

                              The full url that would be built then would be
                              (assuming defaults and using "example.com" and
                              you are using the "ping" view):

                                http://example.com:4040/path/to/subs/ping
        app_name:str         The name of your application.
        api_version:str      The API version you wish to use for your
                            application.  Subsonic will throw an error if you
                            try to use/send an api version higher than what
                            the server supports.  See the Subsonic API docs
                            to find the Subsonic version -> API version table.
                            This is useful if you are connecting to an older
                            version of Subsonic.
        use_netrc:str|bool   You can either specify a specific netrc
                            formatted file or True to use your default
                            netrc file ($HOME/.netrc).
        legacy_auth:bool     Use pre-1.13.0 API version authentication
        use_get:bool         Use a GET request instead of the default POST
                            request.  This is not recommended as request
                            URLs can get very long with some API calls
        use_views:bool       The original Subsonic wanted API clients
                            user the .view end points instead of just the method
                            name. Disable this to drop the .view extension to
                            method name, e.g. ping instead of ping.view
        """
        super().__init__(base_url, username, password, port, api_key, server_path, app_name, api_version,
                       use_netrc, legacy_auth, use_get, use_views)



    # API methods
    async def add_chat_message(self, message:str) -> bool:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/addchatmessage/

        Adds a message to the chat log

        message:str     The message to add

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'addChatMessage'

        q = {'message': message}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def change_password(self, username:str, password:str) -> bool:
        """
        since: 1.1.0

        https://opensubsonic.netlify.app/docs/endpoints/changepassword/

        Changes the password of an existing Subsonic user.  Note that the
        user performing this must have admin privileges

        username:str        The username whose password is being changed
        password:str        The new password of the user

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'changePassword'

        # There seems to be an issue with some subsonic implementations
        # not recognizing the "enc:" precursor to the encoded password and
        # encodes the whole "enc:<hex>" as the password.  Weird.
        #q = {'username': username, 'password': hexPass.lower()}
        q = {'username': username, 'password': password}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def create_bookmark(self, mid:str, position:int, comment:str|None=None) -> bool:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/createbookmark/

        Creates or updates a bookmark (position within a media file).
        Bookmarks are personal and not visible to other users

        mid:str         The ID of the media file to bookmark.  If a bookmark
                        already exists for this file, it will be overwritten
        position:int    The position (in milliseconds) within the media file
        comment:str     A user-defined comment

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'createBookmark'

        q = self._get_query_dict({'id': mid, 'position': position,
            'comment': comment})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def create_internet_radio_station(self, stream_url:str, name:str,
                                      homepage_url:str|None=None) -> bool:
        """
        since 1.16.0

        https://opensubsonic.netlify.app/docs/endpoints/createinternetradiostation/

        Create an internet radio station

        stream_url:str   The stream URL for the station
        name:str        The user-defined name for the station
        homepage_url:str The homepage URL for the station
        """
        method = 'createInternetRadioStation'

        q = self._get_query_dict({
            'streamUrl':stream_url, 'name': name, 'homepageUrl': homepage_url})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def create_playlist(self, playlist_id:str|None=None, name:str|None=None,
                       song_ids:list[str]|None=None) -> bool:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/createplaylist/

        Creates OR updates a playlist.  If updating the list, the
        playlistId is required.  If creating a list, the name is required.

        playlist_id:str     The ID of the playlist to UPDATE
        name:str            The name of the playlist to CREATE
        song_ids:list       The list of songIds to populate the list with in
                            either create or update mode.  Note that this
                            list will replace the existing list if updating

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'createPlaylist'

        if song_ids is None:
            song_ids = []

        if playlist_id == name == None:
            raise errors.ArgumentError('You must supply either a playlistId or a name')
        if playlist_id is not None and name is not None:
            raise errors.ArgumentError('You can only supply either a playlistId '
                 'OR a name, not both')

        q = self._get_query_dict({'playlistId': playlist_id, 'name': name})

        res = await self._do_request_with_list(method, 'songId', song_ids, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def create_podcast_channel(self, url:str) -> bool:
        """
        since: 0.9.0

        https://opensubsonic.netlify.app/docs/endpoints/createpodcastchannel/

        Adds a new Podcast channel.  Note: The user must be authorized
        for Podcast administration

        url:str     The URL of the Podcast to add

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'createPodcastChannel'

        q = {'url': url}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def create_share(self, shids:list[str]|None=None, description:str|None=None,
                     expires:float|None=None) -> Share:
        """
        since: 1.6.0

        https://opensubsonic.netlify.app/docs/endpoints/createshare/

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

        This returns a media.Share
        """
        method = 'createShare'

        if shids is None:
            shids = []

        q = self._get_query_dict({'description': description,
            'expires': self._ts2milli(int(expires or 0))})
        res = await self._do_request_with_list(method, 'id', shids, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return Share.from_dict(dres['shares']['share'][0])


    async def create_user(self, username:str, password:str, email:str,
            ldap_authed:bool=False, admin_role:bool=False,
            settings_role:bool=True, stream_role:bool=True, jukebox_role:bool=False,
            download_role:bool=False, upload_role:bool=False,
            playlist_role:bool=False, cover_art_role:bool=False,
            comment_role:bool=False, podcast_role:bool=False, share_role:bool=False,
            video_conversion_role:bool=False, music_folder_id:int|None=None) -> bool:
        """
        since: 1.1.0

        https://opensubsonic.netlify.app/docs/endpoints/createuser/

        Creates a new subsonic user, using the parameters defined.  See the
        documentation at http://subsonic.org for more info on all the roles.

        username:str        The username of the new user
        password:str        The password for the new user
        email:str           The email of the new user
        <For info on the boolean roles, see http://subsonic.org for more info>
        music_folder_id:int These are the only folders the user has access to

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'createUser'
        hex_pass = f'enc:{self._hex_enc(password)}'

        q = self._get_query_dict({
            'username': username, 'password': hex_pass, 'email': email,
            'ldapAuthenticated': ldap_authed, 'adminRole': admin_role,
            'settingsRole': settings_role, 'streamRole':stream_role,
            'jukeboxRole': jukebox_role, 'downloadRole': download_role,
            'uploadRole': upload_role, 'playlistRole': playlist_role,
            'coverArtRole': cover_art_role, 'commentRole': comment_role,
            'podcastRole': podcast_role, 'shareRole': share_role,
            'videoConversionRole': video_conversion_role,
            'musicFolderId': music_folder_id
        })

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def delete_bookmark(self, mid:str) -> bool:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/deletebookmark/

        Deletes the bookmark for a given file

        mid:str     The ID of the media file to delete the bookmark from.
                    Other users' bookmarks are not affected

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'deleteBookmark'

        q = {'id': mid}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def delete_internet_radio_station(self, iid:str) -> bool:
        """
        since 1.16.0

        https://opensubsonic.netlify.app/docs/endpoints/deleteinternetradiostation/

        Create an internet radio station

        iid:str         The ID for the station
        """
        method = 'deleteInternetRadioStation'

        q = {'id': iid}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def delete_podcast_channel(self, pid:str) -> bool:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/deletepodcastchannel/

        Deletes a Podcast channel.  Note: The user must be authorized
        for Podcast administration

        pid:str         The ID of the Podcast channel to delete

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'deletePodcastChannel'

        q = {'id': pid}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def delete_podcast_episode(self, pid:str) -> bool:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/deletepodcastepisode/

        Deletes a Podcast episode.  Note: The user must be authorized
        for Podcast administration

        pid:str         The ID of the Podcast episode to delete

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'deletePodcastEpisode'

        q = {'id': pid}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def delete_user(self, username:str) -> bool:
        """
        since: 1.3.0

        https://opensubsonic.netlify.app/docs/endpoints/deleteuser/

        Deletes an existing Subsonic user.  Of course, you must have admin
        rights for this.

        username:str        The username of the user to delete

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'deleteUser'

        q = {'username': username}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def delete_playlist(self, pid:str) -> bool:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/deleteplaylist/

        Deletes a saved playlist

        pid:str     ID of the playlist to delete, as obtained by getPlaylists

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'deletePlaylist'

        res = await self._do_request(method, {'id': pid})
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def download(self, sid:str) -> ClientResponse:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/download/

        Downloads a given music file.

        sid:str     The ID of the music file to download.

        Returns the file-like object for reading or raises an exception
        on error
        """
        method = 'download'

        res = await self._do_request(method, {'id': sid})
        dres = await self._handle_bin_res(res)
        if isinstance(dres, dict):
            self._check_status(dres)
        return dres


    async def download_podcast_episode(self, pid:str) -> bool:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/downloadpodcastepisode/

        Tells the server to start downloading a given Podcast episode.
        Note: The user must be authorized for Podcast administration

        pid:str         The ID of the Podcast episode to download

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'downloadPodcastEpisode'

        q = {'id': pid}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def delete_share(self, shid:str) -> bool:
        """
        since: 1.6.0

        https://opensubsonic.netlify.app/docs/endpoints/deleteshare/

        Deletes an existing share

        shid:str        The id of the share to delete

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'deleteShare'

        q = self._get_query_dict({'id': shid})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def get_album(self, album_id:str) -> AlbumID3:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getalbum/

        Returns the info and songs for an album.  This method uses
        the ID3 tags for organization

        album_id:str      The album ID

        Returns a media.AlbumID3
        """
        method = 'getAlbum'

        q = self._get_query_dict({'id': album_id})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return AlbumID3.from_dict(dres['album'])


    async def get_album_info(self, aid:str) -> AlbumInfo:
        """
        since 1.14.0

        Returns the album notes, image URLs, etc., using data from last.fm

        aid:int     The album ID

        Returns media.AlbumInfo
        """
        method = 'getAlbumInfo'

        q = {'id': aid}
        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return AlbumInfo.from_dict(dres['albumInfo'])


    async def get_album_info2(self, aid:str) -> AlbumInfo:
        """
        since 1.14.0

        Same as getAlbumInfo, but uses ID3 tags

        aid:int     The album ID

        Returns media.AlbumInfo
        """
        method = 'getAlbumInfo2'

        q = {'id': aid}
        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return AlbumInfo.from_dict(dres['albumInfo'])


    async def get_album_list(self, ltype:str, size:int=10, offset:int=0, from_year:int|None=None,
            to_year:int|None=None, genre:str|None=None,
            music_folder_id:str|None=None) -> list[Album]:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/getalbumlist/

        Returns a list of random, newest, highest rated etc. albums.
        Similar to the album lists on the home page of the Subsonic
        web interface

        ltype:str       The list type. Must be one of the following: random,
                        newest, highest, frequent, recent,
                        (since 1.8.0 -> )starred, alphabeticalByName,
                        alphabeticalByArtist
                        Since 1.10.1 you can use byYear and byGenre to
                        list albums in a given year range or genre.
        size:int        The number of albums to return. Max 500
        offset:int      The list offset. Use for paging. Max 5000
        from_year:int   If you specify the ltype as "byYear", you *must*
                        specify fromYear
        to_year:int     If you specify the ltype as "byYear", you *must*
                        specify toYear
        genre:str       The name of the genre e.g. "Rock".  You must specify
                        genre if you set the ltype to "byGenre"
        music_folder_id:str Only return albums in the music folder with
                            the given ID. See getMusicFolders()

        Returns a list of media.Album
        """
        method = 'getAlbumList'

        q = self._get_query_dict({'type': ltype, 'size': size,
            'offset': offset, 'fromYear': from_year, 'toYear': to_year,
            'genre': genre, 'musicFolderId': music_folder_id})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        if 'album' not in dres['albumList']:
            return []
        return [Album.from_dict(entry) for entry in dres['albumList']['album']]


    async def get_album_list2(self, ltype:str, size:int=10, offset:int=0,
                      from_year:int|None=None, to_year:int|None=None,
                      genre:str|None=None) -> list[AlbumID3]:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getalbumlist2/

        Returns a list of random, newest, highest rated etc. albums.
        This is similar to getAlbumList, but uses ID3 tags for
        organization

        ltype:str       The list type. Must be one of the following: random,
                        newest, highest, frequent, recent,
                        (since 1.8.0 -> )starred, alphabeticalByName,
                        alphabeticalByArtist
                        Since 1.10.1 you can use byYear and byGenre to
                        list albums in a given year range or genre.
        size:int        The number of albums to return. Max 500
        offset:int      The list offset. Use for paging. Max 5000
        from_year:int   If you specify the ltype as "byYear", you *must*
                        specify fromYear
        to_year:int     If you specify the ltype as "byYear", you *must*
                        specify toYear
        genre:str       The name of the genre e.g. "Rock".  You must specify
                        genre if you set the ltype to "byGenre"

        Returns a list of media.Album
        """
        method = 'getAlbumList2'

        q = self._get_query_dict({'type': ltype, 'size': size,
            'offset': offset, 'fromYear': from_year, 'toYear': to_year,
            'genre': genre})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        if 'album' not in dres['albumList2']:
            return []
        return [AlbumID3.from_dict(entry) for entry in dres['albumList2']['album']]


    async def get_artist(self, artist_id:str) -> ArtistID3:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getartist/

        Returns the info (albums) for an artist.  This method uses
        the ID3 tags for organization

        artist_id:str      The artist ID

        Returns media.Artist
        """
        method = 'getArtist'

        q = self._get_query_dict({'id': artist_id})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return ArtistID3.from_dict(dres['artist'])


    async def get_artists(self) -> Artists:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getartists/

        Similar to getIndexes(), but this method uses the ID3 tags to
        determine the artist

        Returns a media.Artists
        """
        method = 'getArtists'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)

        return Artists.from_dict(dres['artists'])


    async def get_artist_info(self, aid:str, count:int=20,
                        include_not_present:bool=False) -> ArtistInfo:
        """
        since: 1.11.0

        https://opensubsonic.netlify.app/docs/endpoints/getartistinfo/

        Returns a media.ArtistInfo

        aid:str                 The ID of the artist, album or song
        count:int               The max number of similar artists to return
        include_not_present:bool  Whether to return artists that are not
                                present in the media library
        """
        method = 'getArtistInfo'

        q = {'id': aid, 'count': count,
            'includeNotPresent': include_not_present}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return ArtistInfo.from_dict(dres['artistInfo'])


    async def get_artist_info2(self, aid:str, count:int=20,
                         include_not_present:bool=False) -> ArtistInfo2:
        """
        since: 1.11.0

        https://opensubsonic.netlify.app/docs/endpoints/getartistinfo2/

        Similar to getArtistInfo(), but organizes music according to ID3 tags

        aid:str                 The ID of the artist, album or song
        count:int               The max number of similar artists to return
        include_not_present:bool  Whether to return artists that are not
                                present in the media library
        """
        method = 'getArtistInfo2'

        q = {'id': aid, 'count': count,
            'includeNotPresent': include_not_present}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return ArtistInfo2.from_dict(dres['artistInfo2'])


    async def get_avatar(self, username:str) -> ClientResponse:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getavatar/

        Returns the avatar for a user or None if the avatar does not exist

        username:str    The user to retrieve the avatar for

        Returns the aiohttp.ClientResponse object for reading on success or raises
        and exception
        """
        method = 'getAvatar'

        q = {'username': username}

        res = await self._do_request(method, q)
        dres = await self._handle_bin_res(res)
        if isinstance(dres, dict):
            self._check_status(dres)
        return dres


    async def get_bookmarks(self) -> list[Bookmark]:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/getbookmarks/

        Returns all bookmarks for this user.  A bookmark is a position
        within a media file
        """
        method = 'getBookmarks'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return [Bookmark.from_dict(b) for b in dres['bookmarks']['bookmark']]


    async def get_captions(self, vid, fmt=None):
        """
        since 1.14.0

        Returns captions (subtitles) for a video.  Use getVideoInfo for a list
        of captions.

        vid:int         The ID of the video
        fmt:str         Preferred captions format ("srt" or "vtt")
        """
        method = 'getCaptions'

        q = self._get_query_dict({'id':int(vid), 'format': fmt})
        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return dres


    async def get_chat_messages(self, since:int=1) -> list[ChatMessage]:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/getchatmessages/

        Returns the current visible (non-expired) chat messages.

        since:int       Only return messages newer than this timestamp

        NOTE: All times returned are in MILLISECONDS since the Epoch, not
              seconds!

        Returns a list of media.ChatMessage
        """
        method = 'getChatMessages'

        q = {'since': self._ts2milli(since)}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return [ChatMessage.from_dict(dres['chatMessages']['chatMessage'])]


    async def get_cover_art(self, aid:str, size:int|None=None) -> ClientResponse:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/getcoverart/

        Returns a cover art image

        aid:str     ID string for the cover art image to download
        size:int    If specified, scale image to this size

        Returns the file-like object for reading or raises an exception
        on error
        """
        method = 'getCoverArt'

        q = self._get_query_dict({'id': aid, 'size': size})

        res = await self._do_request(method, q, is_stream=True)
        dres = await self._handle_bin_res(res)
        if isinstance(dres, dict):
            self._check_status(dres)
        return dres


    async def get_genres(self) -> list[Genre]:
        """
        since 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/getgenres/

        Returns all genres
        """
        method = 'getGenres'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return [Genre.from_dict(g) for g in dres['genres']['genre']]


    async def get_indexes(self, music_folder_id:int|None=None, if_modified_since:int|None=None) -> Indexes:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/getindexes/

        Returns an indexed structure of all artists

        music_folder_id:int     If this is specified, it will only return
                                artists for the given folder ID from
                                the getMusicFolders call
        if_modified_since:int   If specified, return a result if the artist
                                collection has changed since the given
                                unix timestamp

        Returns a media.Indexes

        """
        method = 'getIndexes'

        q = self._get_query_dict({'musicFolderId': music_folder_id,
            'ifModifiedSince': self._ts2milli(if_modified_since) if if_modified_since else 0})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return Indexes.from_dict(dres['indexes'])


    async def get_internet_radio_stations(self) -> list[InternetRadioStation]:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/getinternetradiostations/

        Returns all internet radio stations
        """
        method = 'getInternetRadioStations'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return [InternetRadioStation.from_dict(i)
                for i in dres['internetRadioStations']['internetRadioStation']]


    async def get_license(self) -> dict:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/getlicense/

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
        method = 'getLicense'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return dres


    async def get_lyrics(self, artist:str|None=None, title:str|None=None) -> Lyrics:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/getlyrics/

        Searches for and returns lyrics for a given song

        artist:str      The artist name
        title:str       The song title

        Returns a 

        """
        method = 'getLyrics'

        q = self._get_query_dict({'artist': artist, 'title': title})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return Lyrics.from_dict(dres['lyrics'])


    async def get_lyrics_by_song_id(self, song_id:str) -> list[StructuredLyrics]:
        """
        Since Open Subsonic ver 1

        https://opensubsonic.netlify.app/docs/endpoints/getlyricsbysongid/

        Retrieves all structured lyrics from the server for a given song.
        The lyrics can come from embedded tags (SYLT/USLT), LRC file/text
        file, or any other external source.

        id:str          The id of the requested songA

        Returns a list of media.StructuredLyrics
        """
        method = 'getLyricsBySongId'

        q = self._get_query_dict({'id': song_id})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return [StructuredLyrics.from_dict(l) for l in dres['lyricsList']['structuredLyrics']]


    async def get_music_directory(self, mid:str) -> Directory:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/getindexes/ 

        Returns a listing of all files in a music directory.  Typically used
        to get a list of albums for an artist or list of songs for an album.

        mid:str     The string ID value which uniquely identifies the
                    folder.  Obtained via calls to getIndexes or
                    getMusicDirectory.  REQUIRED

        Returns a media.Directory
        """
        method = 'getMusicDirectory'

        res = await self._do_request(method, {'id': mid})
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return Directory.from_dict(dres['directory'])


    async def get_music_folders(self) -> list[MusicFolder]:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/getmusicfolders/

        Returns all configured music folders

        Returns a List of media.MusicFolder
        """
        method = 'getMusicFolders'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return [MusicFolder.from_dict(f) for f in dres["musicFolders"]]


    async def get_newest_podcasts(self, count:int=20) -> list[PodcastEpisode]:
        """
        since 1.13.0

        https://opensubsonic.netlify.app/docs/endpoints/getnewestpodcasts/

        Returns the most recently published Podcast episodes as a list of media.PodcastEpisode

        count:int       The number of episodes to return
        """
        method = 'getNewestPodcasts'

        q = {'count': count}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        if 'newestPodcasts' not in dres or 'episode' not in dres['newestPodcasts']:
            return []
        return [PodcastEpisode.from_dict(entry) for entry in dres['newestPodcasts']['episode']]


    async def get_now_playing(self) -> list[NowPlayingEntry]:
        """
        since: 1.0.0

        Returns what is currently being played by all users

        Returns a list of media.NowPlayingEntry
        """
        method = 'getNowPlaying'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return [NowPlayingEntry.from_dict(n) for n in dres['nowPlaying']['entry']]


    async def get_open_subsonic_extensions(self) -> list[OpenSubsonicExtension]:
        """
        since OpenSubsonic 1

        https://opensubsonic.netlify.app/docs/endpoints/getopensubsonicextensions/

        List the OpenSubsonic extensions supported by this server.

        Returns a list of media.OpenSubsonicExtenstion
        """
        method = 'getOpenSubsonicExtensions'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return [OpenSubsonicExtension.from_dict(o) for o in dres['openSubsonicExtensions']]


    async def get_playlist(self, pid:str) -> Playlist:
        """
        since: 1.0.0

        Returns a listing of files in a saved playlist

        id:str      The ID of the playlist as returned in getPlaylists()

        Returns a media.Playlist complete with all tracks

        """
        method = 'getPlaylist'

        res = await self._do_request(method, {'id': pid})
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return Playlist.from_dict(dres['playlist'])


    async def get_playlists(self, username:str|None=None) -> list[Playlist]:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/getplaylists/

        Returns the ID and name of all saved playlists
        The "username" option was added in 1.8.0.

        username:str        If specified, return playlists for this user
                            rather than for the authenticated user.  The
                            authenticated user must have admin role
                            if this parameter is used

        Returns a list of media.Playlist

        note:       The Playlist objects returned are not the full playlist
                    (with tracks) but meant to give the basic details of what
                    playlists are available. For the full object see getPlaylist()
        """
        method = 'getPlaylists'

        q = self._get_query_dict({'username': username})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        if 'playlist' in dres['playlists']:
            return [Playlist.from_dict(entry) for entry in dres['playlists']['playlist']]
        else:
            return [] 


    async def get_play_queue(self) -> PlayQueue:
        """
        since 1.12.0

        https://opensubsonic.netlify.app/docs/endpoints/getplayqueue/

        Returns the state of the play queue for this user (as set by
        savePlayQueue). This includes the tracks in the play queue,
        the currently playing track, and the position within this track.
        Typically used to allow a user to move between different
        clients/apps while retaining the same play queue (for instance
        when listening to an audio book).
        """
        method = 'getPlayQueue'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return PlayQueue.from_dict(dres['playQueue'])


    async def get_podcasts(self, inc_episodes:bool=True, pid:str|None=None) -> list[PodcastChannel]:
        """
        since: 1.6.0

        https://opensubsonic.netlify.app/docs/endpoints/getpodcasts/

        Returns all podcast channels the server subscribes to and their
        episodes.

        inc_episodes:bool    (since: 1.9.0) Whether to include Podcast
                            episodes in the returned result.
        pid:str             (since: 1.9.0) If specified, only return
                            the Podcast channel with this ID.

        Returns a list of media.PodcastChannel
        """
        method = 'getPodcasts'

        q = self._get_query_dict({'includeEpisodes': inc_episodes,
            'id': pid})
        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return [PodcastChannel.from_dict(entry) for entry in dres['podcasts']['channel']]


    async def get_random_songs(self, size:int=10, genre:str|None=None, from_year:int|None=None,
            to_year:int|None=None, music_folder_id:str|None=None) -> list[Child]:
        """
        since 1.2.0

        Returns random songs matching the given criteria

        size:int            The max number of songs to return. Max 500
        genre:str           Only return songs from this genre
        from_year:int       Only return songs after or in this year
        to_year:int         Only return songs before or in this year
        music_folder_id:str Only return songs in the music folder with the
                            given ID.  See getMusicFolders

        Returns a list of media.Child
        """
        method = 'getRandomSongs'

        q = self._get_query_dict({'size': size, 'genre': genre,
            'fromYear': from_year, 'toYear': to_year,
            'musicFolderId': music_folder_id})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return [Child.from_dict(entry) for entry in dres['randomSongs']['song']]


    async def get_scan_status(self) -> ScanStatus:
        """
        since: 1.15.0

        https://opensubsonic.netlify.app/docs/endpoints/getscanstatus/

        returns the current status for media library scanning.
        takes no extra parameters.

        returns a media.ScanStatus

        'scanning' changes to false when a scan is complete
        'count' is the total number of items to be scanned
        """
        method = 'getScanStatus'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return ScanStatus.from_dict(dres['scanstatus'])


    async def get_shares(self) -> list[Share]:
        """
        since: 1.6.0

        https://opensubsonic.netlify.app/docs/endpoints/getshares/

        Returns information about shared media this user is allowed to manage

        Note that entry can be either a single dict or a list of dicts

        Returns a list of media.Share
        """
        method = 'getShares'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return [Share.from_dict(s) for s in dres['shares']['share']]


    async def get_similar_songs(self, iid:str, count:int=50) -> list[Child]:
        """
        since 1.11.0

        https://opensubsonic.netlify.app/docs/endpoints/getsimilarsongs/

        Returns a random collection of songs from the given artist and
        similar artists, using data from last.fm. Typically used for
        artist radio features. As a list of media.Song

        iid:str     The artist, album, or song ID
        count:int   Max number of songs to return
        """
        method = 'getSimilarSongs'

        q = {'id': iid, 'count': count}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        if 'similarSongs' not in dres or 'song' not in dres['similarSongs']:
            return []
        return [Child.from_dict(entry) for entry in dres['similarSongs']['song']]


    async def get_similar_songs2(self, iid:str, count:int=50) -> list[Child]:
        """
        since 1.11.0

        https://opensubsonic.netlify.app/docs/endpoints/getsimilarsongs2/

        Similar to getSimilarSongs(), but organizes music according to
        ID3 tags

        iid:str     The artist, album, or song ID
        count:int   Max number of songs to return
        """
        method = 'getSimilarSongs2'

        q = {'id': iid, 'count': count}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        if 'similarSongs2' not in dres or 'song' not in dres['similarSongs2']:
            return []
        return [Child.from_dict(entry) for entry in dres['similarSongs2']['song']]


    async def get_song(self, sid:str) -> Child:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getsong/

        Returns the info for a song.  This method uses the ID3
        tags for organization

        sid:str      The song ID

        Returns a media.Child
        """
        method = 'getSong'

        q = self._get_query_dict({'id': sid})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return Child.from_dict(dres['song'])


    async def get_songs_by_genre(self, genre:str, count:int=10, offset:int=0,
                           music_folder_id:str|None=None) -> list[Child]:
        """
        since 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/getsongsbygenre/

        Returns list of media.Child in a given genre

        genre:str       The genre, as returned by getGenres()
        count:int       The maximum number of songs to return.  Max is 500
                        default: 10
        offset:int      The offset if you are paging.  default: 0
        musicFolderId:int   Only return dresults from the music folder
                            with the given ID. See getMusicFolders
        """
        method = 'getSongsByGenre'

        q = self._get_query_dict({'genre': genre,
            'count': count,
            'offset': offset,
            'musicFolderId': music_folder_id,
        })

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return [Child.from_dict(entry) for entry in dres['songsByGenre']['song']]


    async def get_starred(self, music_folder_id:str|None=None) -> Starred:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getstarred/

        music_folder_id:str   Only return dresults from the music folder
                            with the given ID. See getMusicFolders

        Returns a media.Starred
        """
        method = 'getStarred'

        q = {}
        if music_folder_id:
            q['musicFolderId'] = music_folder_id

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return Starred.from_dict(dres['starred'])


    async def get_starred2(self, music_folder_id:str|None=None) -> Starred2:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getstarred2/

        music_folder_id:int   Only return dresults from the music folder
                            with the given ID. See getMusicFolders

        Returns starred songs, albums and artists like getStarred(),
        but this uses ID3 tags for organization

        Returns a media.Starred2
        """
        method = 'getStarred2'

        q = {}
        if music_folder_id:
            q['musicFolderId'] = music_folder_id

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return Starred2.from_dict(dres['starred2'])


    async def get_top_songs(self, artist:str, count:int=50) -> list[Child]:
        """
        since 1.13.0

        https://opensubsonic.netlify.app/docs/endpoints/gettopsongs/

        Returns the top songs for a given artist as a List of media.Song

        artist:str      The artist to get songs for
        count:int       The number of songs to return
        """
        method = 'getTopSongs'

        q = {'artist': artist, 'count': count}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        if 'topSongs' not in dres or 'song' not in dres['topSongs']:
            return []
        return [Child.from_dict(entry) for entry in dres['topSongs']['song']]


    async def get_user(self, username:str) -> User:
        """
        since: 1.3.0

        https://opensubsonic.netlify.app/docs/endpoints/getuser/

        Get details about a given user, including which auth roles it has.
        Can be used to enable/disable certain features in the client, such
        as jukebox control

        username:str        The username to retrieve.  You can only retrieve
                            your own user unless you have admin privs.

        Returns a media.User
        """
        method = 'getUser'

        q = {'username': username}

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return User.from_dict(dres['user'])


    async def get_users(self) -> list[User]:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/getusers/

        Gets a list of users

        returns a list of media.User

        """
        method = 'getUsers'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return [User.from_dict(u) for u in dres['users']['user']]


    async def get_videos(self) -> dict:
        """
        since 1.8.0

        Returns all video files

        Returns a dict
        """
        method = 'getVideos'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return dres


    async def get_video_info(self, vid):
        """
        since 0.14.0

        Returns details for a video, including information about available
        audio tracks, subtitles (captions) and conversions.

        vid:int     The video ID
        """
        method = 'getVideoInfo'

        q = {'id':int(vid)}
        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return dres


    async def hls (self, mid, bitrate=None):
        """
        since 0.8.0

        Creates an HTTP live streaming playlist for streaming video or
        audio HLS is a streaming protocol implemented by Apple and
        works by breaking the overall stream into a sequence of small
        HTTP-based file downloads. It's supported by iOS and newer
        versions of Android. This method also supports adaptive
        bitrate streaming, see the bitRate parameter.

        mid:str     The ID of the media to stream
        bitrate:str If specified, the server will attempt to limit the
                    bitrate to this value, in kilobits per second. If
                    this parameter is specified more than once, the
                    server will create a variant playlist, suitable
                    for adaptive bitrate streaming. The playlist will
                    support streaming at all the specified bitrates.
                    The server will automatically choose video dimensions
                    that are suitable for the given bitrates.
                    (since: 0.9.0) you may explicitly request a certain
                    width (479) and height (360) like so:
                    bitRate=999@480x360

        Returns the raw m2u8 file as a string
        """
        method = 'hls'

        q = self._get_query_dict({'id': mid, 'bitrate': bitrate})
        res = await self._do_request(method, q)
        dres = await self._handle_bin_res(res)
        if isinstance(dres, dict):
            self._check_status(dres)
        return dres.content


    async def jukebox_control(self, action:str, index:int|None=None, sids:list[str]|None=None,
                       gain:float|None=None, offset:int|None=None) -> JukeboxStatus|JukeboxPlaylist:
        """
        since: 1.2.0

        https://opensubsonic.netlify.app/docs/endpoints/jukeboxcontrol/

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
        sids:list[str]  Used by "add" and "set". ID of song to add to the
                        jukebox playlist. Use multiple id parameters to
                        add many songs in the same request.  Whether you
                        are passing one song or many into this, this
                        parameter MUST be a list
        gain:float      Used by setGain to control the playback volume.
                        A float value between 0.0 and 1.0
        offset:int      (added in API 1.7.0) Used by "skip".  Start playing
                        this many seconds into the track.

        Returns a media.JukeboxPlaylist if action == 'get', JukeboxStatus otherwise
        """
        method = 'jukeboxControl'

        if sids is None:
            sids = []

        q = self._get_query_dict({'action': action, 'index': index,
            'gain': gain, 'offset': offset})

        res = None
        if action == 'add':
            # We have to deal with the sids
            if not (isinstance(sids, list) or isinstance(sids, tuple)):
                raise errors.ArgumentError('If you are adding songs, "sids" must '
                    'be a list or tuple!')
            res = await self._do_request_with_list(method, 'id', sids, q)
        else:
            res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)

        if action == 'get':
            return JukeboxPlaylist.from_dict(dres['jukeboxPlaylist'])

        return JukeboxStatus.from_dict(dres['jukeboxStatus'])


    async def ping(self) -> bool:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/ping/

        Returns a boolean True if the server is alive, raises the returned error
        """
        method = 'ping'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        if dres['status'] == 'ok':
            return True
        elif dres['status'] == 'failed':
            err = Error.from_dict(dres['error'])
            exc = errors.getExcByCode(err.code)
            raise exc(err.message)
        return False


    async def refresh_podcasts(self) -> bool:
        """
        since: 1.9.0

        https://opensubsonic.netlify.app/docs/endpoints/refreshpodcasts/

        Tells the server to check for new Podcast episodes. Note: The user
        must be authorized for Podcast administration

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'refreshPodcasts'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def save_play_queue(self, qids, current=None, position=None) -> bool:
        """
        since 0.12.0

        https://opensubsonic.netlify.app/docs/endpoints/saveplayqueue/

        qid:list[int]       The list of song ids in the play queue
        current:int         The id of the current playing song
        position:int        The position, in milliseconds, within the current
                            playing song

        Saves the state of the play queue for this user. This includes
        the tracks in the play queue, the currently playing track, and
        the position within this track. Typically used to allow a user to
        move between different clients/apps while retaining the same play
        queue (for instance when listening to an audio book).
        """
        method = 'savePlayQueue'

        if not isinstance(qids, (tuple, list)):
            qids = [qids]

        q = self._get_query_dict({'current': current, 'position': position})

        res = await self._do_request_with_lists(method, {'id': qids}, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def scrobble(self, sid:str, submission:bool=True, listen_time:int|None=None) -> bool:
        """
        since: 1.5.0

        https://opensubsonic.netlify.app/docs/endpoints/scrobble/

        "Scrobbles" a given music file on last.fm.  Requires that the user
        has set this up.

        Since 1.8.0 you may specify multiple id (and optionally time)
        parameters to scrobble multiple files.

        Since 1.11.0 this method will also update the play count and
        last played timestamp for the song and album. It will also make
        the song appear in the "Now playing" page in the web app, and
        appear in the list of songs returned by getNowPlaying

        sid:str             The ID of the file to scrobble
        submission:bool     Whether this is a "submission" or a "now playing"
                            notification
        listenTime:int      (Since 1.8.0) The time (unix timestamp) at
                            which the song was listened to.

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'scrobble'

        q = self._get_query_dict({'id': sid, 'submission': submission,
            'time': self._ts2milli(listen_time)})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def search2(self, query:str, artist_count:int=20, artist_offset:int=0,
                album_count:int=20, album_offset:int=0, song_count:int=20,
                song_offset:int=0, music_folder_id:int|None=None) -> SearchResult2:
        """
        since: 1.4.0

        https://opensubsonic.netlify.app/docs/endpoints/search2/

        Returns albums, artists and songs matching the given search criteria.
        Supports paging through the result.

        query:str           The search query
        artist_count:int    Max number of artists to return [default: 20]
        artist_offset:int   Search offset for artists (for paging) [default: 0]
        album_count:int     Max number of albums to return [default: 20]
        album_offset:int    Search offset for albums (for paging) [default: 0]
        song_count:int      Max number of songs to return [default: 20]
        song_offset:int     Search offset for songs (for paging) [default: 0]
        music_folder_id:int Only return dresults from the music folder
                            with the given ID. See getMusicFolders

        Returns a media.SearchResult2
        """
        method = 'search2'

        q = self._get_query_dict({'query': query, 'artistCount': artist_count,
            'artistOffset': artist_offset, 'albumCount': album_count,
            'albumOffset': album_offset, 'songCount': song_count,
            'songOffset': song_offset, 'musicFolderId': music_folder_id})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return SearchResult2.from_dict(dres['searchResult2'])


    async def search3(self, query:str, artist_count:int=20, artist_offset:int=0,
                album_count:int=20, album_offset:int=0, song_count:int=20,
                song_offset:int=0, music_folder_id:int|None=None) -> SearchResult3:
        """
        since: 1.8.0

        Works the same way as search2, but uses ID3 tags for
        organization

        https://opensubsonic.netlify.app/docs/endpoints/search3/

        query:str           The search query
        artist_count:int    Max number of artists to return [default: 20]
        artist_offset:int   Search offset for artists (for paging) [default: 0]
        album_count:int     Max number of albums to return [default: 20]
        album_offset:int    Search offset for albums (for paging) [default: 0]
        song_count:int      Max number of songs to return [default: 20]
        song_offset:int     Search offset for songs (for paging) [default: 0]
        music_folder_id:int Only return dresults from the music folder
                            with the given ID. See getMusicFolders

        Returns a media.SearchResult3
        """
        method = 'search3'

        q = self._get_query_dict({'query': query, 'artistCount': artist_count,
            'artistOffset': artist_offset, 'albumCount': album_count,
            'albumOffset': album_offset, 'songCount': song_count,
            'songOffset': song_offset, 'musicFolderId': music_folder_id})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return SearchResult3.from_dict(dres['searchResult3'])


    async def set_rating(self, item_id:str, rating:int) -> bool:
        """
        since: 1.6.0

        https://opensubsonic.netlify.app/docs/endpoints/setrating/

        Sets the rating for a music file

        item_id:str          The id of the item (song/artist/album) to rate
        rating:int      The rating between 1 and 5 (inclusive), or 0 to remove
                        the rating

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'setRating'

        try:
            rating = int(rating)
        except Exception as exc:
            raise errors.ArgumentError(
                f'Rating must be an integer between 0 and 5: {rating}') from exc
        if rating < 0 or rating > 5:
            raise errors.ArgumentError(
                f'Rating must be an integer between 0 and 5: {rating}')

        q = self._get_query_dict({'id': item_id, 'rating': rating})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def star(self, sids:list[str]|None=None, album_ids:list[str]|None=None,
             artist_ids:list[str]|None=None) -> bool:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/star/

        Attaches a star to songs, albums or artists

        sids:list       A list of song IDs to star
        album_ids:list  A list of album IDs to star.  Use this rather than
                        "sids" if the client access the media collection
                        according to ID3 tags rather than file
                        structure
        artist_ids:list  The ID of an artist to star.  Use this rather
                        than sids if the client access the media
                        collection according to ID3 tags rather
                        than file structure

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'star'

        if sids is None:
            sids = []
        if album_ids is None:
            album_ids = []
        if artist_ids is None:
            artist_ids = []

        list_map = {'id': sids,
            'albumId': album_ids,
            'artistId': artist_ids}
        res = await self._do_request_with_lists(method, list_map)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def start_scan(self) -> ScanStatus:
        """
        since: 1.15.0

        https://opensubsonic.netlify.app/docs/endpoints/startscan/

        Initiates a rescan of the media libraries.
        Takes no extra parameters.

        returns a media.ScanStatus

        'scanning' changes to false when a scan is complete
        'count' starts a 0 and ends at the total number of items scanned

        """
        method = 'startScan'

        res = await self._do_request(method)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return ScanStatus.from_dict(dres['scanstatus'])


    async def stream(self, sid:str, max_bit_rate:int=0, tformat:str|None=None,
               time_offset:int|None=None, size:str|None=None,
               estimate_length:bool=False, converted:bool=False) -> ClientResponse:
        """
        since: 1.0.0

        https://opensubsonic.netlify.app/docs/endpoints/stream/

        Downloads a given music file.

        sid:str         The ID of the music file to download.
        max_bit_rate:int (since: 1.2.0) If specified, the server will
                        attempt to limit the bitrate to this value, in
                        kilobits per second. If set to zero (default), no limit
                        is imposed. Legal values are: 0, 32, 40, 48, 56, 64,
                        80, 96, 112, 128, 160, 192, 224, 256 and 320.
        tformat:str     (since: 1.6.0) Specifies the target format
                        (e.g. "mp3" or "flv") in case there are multiple
                        applicable transcodings (since: 1.9.0) You can use
                        the special value "raw" to disable transcoding
        time_offset:int (since: 1.6.0) Only applicable to video
                        streaming.  Start the stream at the given
                        offset (in seconds) into the video
        size:str        (since: 1.6.0) The requested video size in
                        WxH, for instance 640x480
        estimate_length:bool       (since: 1.8.0) If set to True,
                                    the HTTP Content-Length header
                                    will be set to an estimated
                                    value for trancoded media
        converted:bool  (since: 1.14.0) Only applicable to video streaming.
                        Subsonic can optimize videos for streaming by
                        converting them to MP4. If a conversion exists for
                        the video in question, then setting this parameter
                        to "true" will cause the converted video to be
                        returned instead of the original.

        Returns the file-like object for reading or raises an exception
        on error
        """
        method = 'stream'

        q = self._get_query_dict({'id': sid, 'maxBitRate': max_bit_rate,
            'format': tformat, 'timeOffset': time_offset, 'size': size,
            'estimateContentLength': estimate_length,
            'converted': converted})

        res = await self._do_request(method, q, is_stream=True)
        dres = await self._handle_bin_res(res)
        if isinstance(dres, dict):
            self._check_status(dres)
        return dres


    async def unstar(self, sids:list[str]|None=None, album_ids:list[str]|None=None,
               artist_ids:list[str]|None=None) -> bool:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/unstar/

        Removes a star to songs, albums or artists.  Basically, the
        same as star in reverse

        sids:list       A list of song IDs to star
        album_ids:list  A list of album IDs to star.  Use this rather than
                        "sids" if the client access the media collection
                        according to ID3 tags rather than file
                        structure
        artist_ids:list The ID of an artist to star.  Use this rather
                        than sids if the client access the media
                        collection according to ID3 tags rather
                        than file structure

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'unstar'

        if sids is None:
            sids = []
        if album_ids is None:
            album_ids = []
        if artist_ids is None:
            artist_ids = []

        list_map = {'id': sids,
            'albumId': album_ids,
            'artistId': artist_ids}
        res = await self._do_request_with_lists(method, list_map)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def update_internet_radio_station(self, iid:str, stream_url:str, name:str,
            homepage_url:str|None=None) -> bool:
        """
        since 1.16.0

        https://opensubsonic.netlify.app/docs/endpoints/updateinternetradiostation/

        Create an internet radio station

        iid:str         The ID for the station
        stream_url:str   The stream URL for the station
        name:str        The user-defined name for the station
        homepage_url:str The homepage URL for the station
        """
        method = 'updateInternetRadioStation'

        q = self._get_query_dict({
            'id': iid, 'streamUrl':stream_url, 'name': name,
            'homepageUrl': homepage_url,
        })

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def update_playlist(self, lid:str, name:str|None=None, comment:str|None=None,
                       song_ids_to_add:list[str]|None=None,
                       song_indices_to_remove:list[int]|None=None) -> bool:
        """
        since 1.8.0

        https://opensubsonic.netlify.app/docs/endpoints/updateplaylist/

        Updates a playlist.  Only the owner of a playlist is allowed to
        update it.

        lid:str                 The playlist id
        name:str                The human readable name of the playlist
        comment:str             The playlist comment
        song_ids_to_add:list       A list of song IDs to add to the playlist
        song_indices_to_remove:list Remove the songs at the
                                    0 BASED INDEXED POSITIONS in the
                                    playlist, NOT the song ids.  Note that
                                    this is always a list.

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'updatePlaylist'

        if song_ids_to_add is None:
            song_ids_to_add = []

        if song_indices_to_remove is None:
            song_indices_to_remove = []

        q = self._get_query_dict({'playlistId': lid, 'name': name,
            'comment': comment})
        list_map = {'songIdToAdd': song_ids_to_add,
            'songIndexToRemove': song_indices_to_remove}
        res = await self._do_request_with_lists(method, list_map, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def update_share(self, shid:str, description:str|None=None, expires:float|None=None) -> bool:
        """
        since: 1.6.0

        https://opensubsonic.netlify.app/docs/endpoints/updateshare/

        Updates the description and/or expiration date for an existing share

        shid:str            The id of the share to update
        description:str     The new description for the share (optional).
        expires:float       The new timestamp for the expiration time of this
                            share (optional).

        Returns True on success
        """
        method = 'updateShare'

        q = self._get_query_dict({'id': shid, 'description': description,
            expires: self._ts2milli(int(expires or 0))})

        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    async def update_user(self, username:str,  password:str|None=None, email:str|None=None,
            ldap_authed:bool=False, admin_role:bool=False,
            settings_role:bool=True, stream_role:bool=True, jukebox_role:bool=False,
            download_role:bool=False, upload_role:bool=False,
            playlist_role:bool=False, cover_art_role:bool=False,
            comment_role:bool=False, podcast_role:bool=False, share_role:bool=False,
            video_conv_role:bool=False, music_folder_id:int|None=None,
            max_bit_rate:int=0) -> bool:
        """
        since 1.10.1

        https://opensubsonic.netlify.app/docs/endpoints/updateuser/

        Modifies an existing Subsonic user.

        username:str        The username of the user to update.
        musicFolderId:int   Only return dresults from the music folder
                            with the given ID. See getMusicFolders
        maxBitRate:int      The max bitrate for the user.  0 is unlimited

        All other args are the same as create user and you can update
        whatever item you wish to update for the given username.

        Returns True on success, raises a errors.SonicError or subclass on
        failure.
        """
        method = 'updateUser'
        if password is not None:
            password = f'enc:{self._hex_enc(password)}'
        q = self._get_query_dict({'username': username, 'password': password,
            'email': email, 'ldapAuthenticated': ldap_authed,
            'adminRole': admin_role,
            'settingsRole': settings_role, 'streamRole':stream_role,
            'jukeboxRole': jukebox_role, 'downloadRole': download_role,
            'uploadRole': upload_role, 'playlistRole': playlist_role,
            'coverArtRole': cover_art_role, 'commentRole': comment_role,
            'podcastRole': podcast_role, 'shareRole': share_role,
            'videoConversionRole': video_conv_role,
            'musicFolderId': music_folder_id, 'maxBitRate': max_bit_rate
        })
        res = await self._do_request(method, q)
        dres = await self._handle_info_res(res)
        self._check_status(dres)
        return True


    #
    # Private internal methods
    #
    async def _do_request(self, method:str, query:dict|None=None, is_stream:bool=False) -> ClientResponse:
        qdict = self._get_base_qdict()
        if query is not None:
            qdict.update(query)

        if self._use_views:
            method += '.view'
        url = f"{self._base_url}:{self._port}/{self._server_path}/{method}"

        if not hasattr(self, "_sess"):
            timeout = ClientTimeout(total=None, sock_connect=30, sock_read=60)
            self._sess = aiohttp.ClientSession(timeout=timeout)

        if self._use_get:
            return await self._sess.get(url, params=qdict)
        return await self._sess.post(url, data=qdict)



    async def _do_request_with_list(self, method:str, list_name:str, alist:list,
                           query:dict|None=None) -> ClientResponse:
        """
        Like _getRequest, but allows appending a number of items with the
        same key (listName).  This bypasses the limitation of urlencode()
        """
        qdict = self._get_base_qdict()
        if query is not None:
            qdict.update(query)
        qdict[list_name] = alist

        if self._use_views:
            method += '.view'
        url = f"{self._base_url}:{self._port}/{self._server_path}/{method}"

        if not hasattr(self, "_sess"):
            timeout = ClientTimeout(total=None, sock_connect=30, sock_read=60)
            self._sess = aiohttp.ClientSession(timeout=timeout)

        if self._use_get:
            return await self._sess.get(url, params=qdict)
        return await self._sess.post(url, data=qdict)


    async def _do_request_with_lists(self, method:str, list_map:dict, query:dict|None=None) -> ClientResponse:
        """
        Like _getRequestWithList(), but you must pass a dictionary
        that maps the listName to the list.  This allows for multiple
        list parameters to be used, like in updatePlaylist()

        method:str        The name of the method
        listMap:dict        A mapping of listName to a list of entries
        query:dict          The normal query dict
        """
        qdict = self._get_base_qdict()
        if query is not None:
            qdict.update(query)
        qdict.update(list_map)

        if self._use_views:
            method += '.view'

        url = f"{self._base_url}:{self._port}/{self._server_path}/{method}"

        if not hasattr(self, "_sess"):
            timeout = ClientTimeout(total=None, sock_connect=30, sock_read=60)
            self._sess = aiohttp.ClientSession(timeout=timeout)

        if self._use_get:
            return await self._sess.get(url, params=qdict)
        return await self._sess.post(url, data=qdict)


    async def _handle_info_res(self, res: ClientResponse) -> dict:
        # Returns a parsed dictionary version of the result
        res.raise_for_status()
        data = await res.json()
        dres = data["subsonic-response"]
        self._check_status(dres)
        return dres


    async def _handle_bin_res(self, res: ClientResponse) -> ClientResponse:
        res.raise_for_status()
        ct = res.headers.get("Content-Type","")
        if ct.startswith("application/json") or ct.startswith("text/html"):
            data = await res.json()
            dres = data["subsonic-response"]
            self._check_status(dres)
            raise
        return res