# -*- coding: utf-8 -*-
'''Version information.'''
'''
  Kontalk Pyserver
  Copyright (C) 2011 Kontalk Devteam <devteam@kontalk.org>

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

NAME = "Kontalk Pyserver Daemon"
PACKAGE = "kontalk-pyserver"
VERSION = "2.6"
AUTHORS = (
    {
        "name": "Daniele Ricci",
        "email" : "daniele.athome@gmail.com"
    },
)

'''Supported s2s protocol'''
SERVER_PROTOCOL = 1
'''Supported c2s protocol'''
CLIENT_PROTOCOL = 4
'''Default c2s protocol if not explicitly declared from client'''
DEFAULT_CLIENT_PROTOCOL = 3

