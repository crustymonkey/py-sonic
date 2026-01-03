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

from abc import ABC, abstractmethod
from netrc import netrc
from hashlib import md5
import os
from typing import TypeVar, Generic, Union, Awaitable

from . import errors


API_VERSION = '1.16.1'


ResponseT = TypeVar("ResponseT")


class ConnBase(ABC, Generic[ResponseT]):
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
        self.set_base_url(base_url)
        self._username = username
        self._raw_pass = password
        self._api_key = api_key
        self._legacy_auth = legacy_auth
        self._use_get = use_get
        self._use_views = use_views
        self._api_version = api_version

        self._netrc = None
        if use_netrc is not None:
            self._process_netrc(use_netrc)
        elif (username is None or password is None) and api_key is None:
            raise errors.CredentialError('You must specify either a username/password '
                'combination, api key with the api_key parameter or "use_netrc" must be either True or a string '
                'representing a path to a netrc file')
        elif username is not None and password is not None and api_key is not None:
            raise errors.CredentialError('You must specify either username and password or api key')

        self.set_port(port)
        self.set_app_name(app_name)
        self.set_server_path(server_path)


    # Properties
    def set_base_url(self, url:str) -> None:
        """ Set our base URL. """
        self._base_url = url
        if '://' in url:
            self._hostname = url.split('://')[1].strip()
        else:
            self._hostname = url
    base_url = property(lambda s: s._base_url, set_base_url)


    def set_port(self, port:int) -> None:
        """ Set the port to use. """
        self._port = port
    port = property(lambda s: s._port, set_port)


    def set_username(self, username:str) -> None:
        """ Set our username. """
        self._username = username
    username = property(lambda s: s._username, set_username)


    def set_password(self, password:str) -> None:
        """ Set our password. """
        self._raw_pass = password
        # Redo the opener with the new creds
    password = property(lambda s: s._raw_pass, set_password)


    api_version = property(lambda s: s._api_version)


    def set_api_key(self, api_key:str) -> None:
        """ Set api key. """
        self._api_key = api_key
    api_key = property(lambda s: s._api_key, set_api_key)


    def set_app_name(self, app_name:str) -> None:
        """ Set the app name. """
        self._app_name = app_name
    app_name = property(lambda s: s._app_name, set_app_name)


    def set_server_path(self, path:str) -> None:
        """ Set our server path. """
        sep = ''
        if path != '' and not path.endswith('/'):
            sep = '/'
        self._server_path = f"{path}{sep}rest".strip('/')
    server_path = property(lambda s: s._server_path, set_server_path)


    def set_legacy_auth(self, lauth:bool) -> None:
        """ Set the legacy_auth field. """
        self._legacy_auth = lauth
    legacy_auth = property(lambda s: s._legacy_auth, set_legacy_auth)


    def set_get(self, g:bool) -> None:
        """ Set use_get field. """
        self._use_get = g
    use_get = property(lambda s: s._use_get, set_get)


    #@deprecated("The search method has been deprecated since 1.4.0, use search[2|3] instead")
    def search(self, artist=None, album=None, title=None, dummy=None,
            count=20, offset=0, newer_than=None):
        """
        since: 1.0.0

        DEPRECATED SINCE API 1.4.0!  USE search3() INSTEAD!
        """
        raise NotImplementedError("search is deprecated in favor of search2 or search3")


    #
    # Private internal methods
    #
    def _get_query_dict(self, d:dict) -> dict:
        """
        Given a dictionary, it cleans out all the values set to None
        """
        for k, v in list(d.items()):
            if v is None:
                del d[k]
        return d


    def _get_base_qdict(self) -> dict:
        qdict = {
            'f': 'json',
            'v': self._api_version,
            'c': self._app_name,
        }

        if self._api_key:
            qdict['apiKey']  = self._api_key
        else:
            qdict['u'] = self._username
            if self._legacy_auth:
                qdict['p'] = f'enc:{self._hex_enc(self._raw_pass)}'
            else:
                salt = self._get_salt()
                token = md5((self._raw_pass + salt).encode('utf-8')).hexdigest()
                qdict.update({
                    's': salt,
                    't': token,
                })

        return qdict


    @abstractmethod
    def _do_request(self, method:str, query:dict|None=None, is_stream:bool=False) -> Union[ResponseT, Awaitable[ResponseT]]:
        pass


    @abstractmethod
    def _do_request_with_list(self, method:str, list_name:str, alist:list,
                           query:dict|None=None) -> Union[ResponseT, Awaitable[ResponseT]]:
        """
        Like _getRequest, but allows appending a number of items with the
        same key (listName).  This bypasses the limitation of urlencode()
        """
        pass


    @abstractmethod
    def _do_request_with_lists(self, method:str, list_map:dict, query:dict|None=None) -> Union[ResponseT, Awaitable[ResponseT]]:
        """
        Like _getRequestWithList(), but you must pass a dictionary
        that maps the listName to the list.  This allows for multiple
        list parameters to be used, like in updatePlaylist()

        method:str        The name of the method
        listMap:dict        A mapping of listName to a list of entries
        query:dict          The normal query dict
        """
        pass


    @abstractmethod
    def _handle_info_res(self, res: ResponseT) -> Union[dict, Awaitable[dict]]:
        # Returns a parsed dictionary version of the result
        pass


    @abstractmethod
    def _handle_bin_res(self, res: ResponseT) -> Union[ResponseT, Awaitable[ResponseT]]:
        pass


    def _check_status(self, result:dict) -> bool:
        if result['status'] == 'failed':
            exc = errors.getExcByCode(result['error']['code'])
            raise exc(result['error']['message'])
        return True


    def _hex_enc(self, raw:str) -> str:
        """
        Returns a "hex encoded" string per the Subsonic api docs

        raw:str     The string to hex encode
        """
        ret = ''
        for c in raw:
            ret += f'{ord(c):02X}'
        return ret


    def _ts2milli(self, ts:int | None) -> int | None:
        """
        For whatever reason, Subsonic uses timestamps in milliseconds since
        the unix epoch.  I have no idea what need there is of this precision,
        but this will just multiply the timestamp times 1000 and return the int
        """
        if ts is None:
            return None
        return int(ts * 1000)


    def _fix_last_modified(self, data):
        """
        This will recursively walk through a data structure and look for
        a dict key/value pair where the key is "lastModified" and change
        the shitty java millisecond timestamp to a real unix timestamp
        of SECONDS since the unix epoch.  JAVA SUCKS!
        """
        if isinstance(data, dict):
            for k, v in list(data.items()):
                if k == 'lastModified':
                    data[k] = int(v) / 1000.0
                    return data
                elif isinstance(v, (tuple, list, dict)):
                    return self._fix_last_modified(v)
        elif isinstance(data, (list, tuple)):
            for item in data:
                if isinstance(item, (list, tuple, dict)):
                    return self._fix_last_modified(item)


    def _process_netrc(self, use_netrc:str):
        """
        The use_netrc var is either a boolean, which means we should use
        the user's default netrc, or a string specifying a path to a
        netrc formatted file

        use_netrc:bool|str      Either set to True to use the user's default
                                netrc file or a string specifying a specific
                                netrc file to use
        """
        if not use_netrc:
            raise errors.CredentialError('use_netrc must be either a boolean "True" '
                'or a string representing a path to a netrc file, '
                f'not {repr(use_netrc)}')
        if isinstance(use_netrc, bool) and use_netrc:
            self._netrc = netrc()
        else:
            # This should be a string specifying a path to a netrc file
            self._netrc = netrc(os.path.expanduser(use_netrc))
        auth = self._netrc.authenticators(self._hostname)
        if not auth:
            raise errors.CredentialError(f'No machine entry found for {self._hostname} in '
                'your netrc file')

        # If we get here, we have credentials
        self._username = auth[0]
        self._raw_pass = auth[2]


    def _get_salt(self, length=16):
        salt = md5(os.urandom(100)).hexdigest()
        return salt[:length]
