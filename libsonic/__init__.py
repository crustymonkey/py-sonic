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

import json

class Connection(object):
    def __init__(self , baseUrl , username , password , apiVersion='1.5.0' ,
            appName='py-sonic'):
        self.baseUrl = baseUrl
        self.username = username
        self.rawPass = password
        self.apiVersion = apiVersion
        self.appName = appName
        
