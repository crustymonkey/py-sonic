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
import json , urllib2

class Connection(object):
    def __init__(self , baseUrl , username , password , port=4040 , 
            apiVersion='1.5.0' , appName='py-sonic'):
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

    port = property(lambda s: s._port , lambda s , p: s._port = int(p))

    def setUsername(self , username):
        self._username = username
        self._opener = self._getOpener(self._username , self._rawPass)
    username = property(lambda s: s._username , setUsername)

    def setPassword(self , password):
        self._rawPass = password
        # Redo the opener with the new creds
        self._opener = self._getOpener(self._username , self._rawPass)
    password = property(lambda s: s._rawPass , setPassword)

    apiVersion = property(lambda s: s._apiVersion , 
            lambda s , v: s._apiVersion = v)

    appName = property(lambda s: s._appName , lambda s , n: s._appName = n)

    # API methods
    def ping(self):
        """
        Returns a boolean True if the server is alive
        """
        req = self._getRequest('ping.view')
        try:
            res = self._opener.open(req)
        except:
            return False
        return res

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
