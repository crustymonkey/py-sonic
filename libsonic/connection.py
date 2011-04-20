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
from errors import VersionError
import json , urllib2

class Connection(object):
    def __init__(self , baseUrl , username , password , port=4040 , 
            apiVersion='1.5.0' , appName='py-sonic'):
        """
        This will create a connection to your subsonic server

        baseUrl:str         The base url for your server. Be sure to use 
                            "https" for SSL connections
                            ex: http://subsonic.example.com
        username:str        The username to use for the connection
        password:str        The password to use for the connection
        port:int            The port number to connect on.  The default for
                            unencrypted subsonic connections is 4040
        apiVersion:str      This is the apiVersion to use.  Different versions
                            of subsonic use different apiVersions.  See
                            the "Versions" section at 
                            http://www.subsonic.org/pages/api.jsp
        appName:str         The name of your application.
        """
        self._baseUrl = baseUrl
        self._username = username
        self._rawPass = password
        self._port = int(port)
        self._apiVersion = apiVersion
        self._appName = appName
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

    def setApiVersion(self , version):
        self._apiVersion = version
    apiVersion = property(lambda s: s._apiVersion , setApiVersion)

    def setAppName(self , appName):
        self._appName = appName
    appName = property(lambda s: s._appName , setAppName)

    # API methods
    def ping(self):
        """
        Returns a boolean True if the server is alive
        """
        since = '1.0.0'
        methodName = 'ping'
        viewName = '%s.view' % methodName
        self._checkVersion(methodName , since)

        req = self._getRequest(viewName)
        try:
            res = self._doInfoReq(req)
        except:
            return False
        if res['status'] == 'ok':
            return True
        return False

    def getLicense(self):
        since = '1.0.0'

    # Private internal methods
    def _getOpener(self , username , passwd):
        creds = b64encode('%s:%s' % (username , passwd))
        opener = urllib2.build_opener()
        if self._baseUrl.startswith('https'):
            opener.add_handler(urllib2.HTTPSHandler())
        opener.addheaders = [('Authorization' , 'Basic %s' % creds)]
        return opener

    def _getRequest(self , viewName , query={} , data=None):
        qstring = {'f': 'json' , 'v': self._apiVersion , 'c': self._appName}
        qstring.update(query)
        url = '%s:%d/rest/%s?%s' % (self._baseUrl , self._port , viewName ,
            urlencode(qstring))
        req = urllib2.Request(url)
        if data:
            req.add_data(data)
        return req

    def _checkVersion(self , methodName , version):
        """
        Raise an exception if the api call is not implemented at this 
        apiVersion
        """
        if self._apiVersion < version:
            raise VersionError('The apiVersion, %s, does not support the '
                '"%s" call (need %s)' % (self._apiVersion , methodName ,
                version)

    def _doInfoReq(self , req):
        # Returns a parsed dictionary version of the result
        res = self._opener.open(req)
        dres = json.loads(res.read())
        return dres['subsonic-response']

    def _doBinReq(self , req):
        res = self._opener.open(req)
        contType = res.info().getheader('Content-Type')
        if contType.startswith('text/html') or \
                contType.startswith('application/json'):
            dres = json.loads(res.read())
            return dres['subsonic-response']
        return res
