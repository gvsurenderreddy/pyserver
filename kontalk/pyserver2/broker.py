# -*- coding: utf-8 -*-
'''The Message Broker Service.'''
'''
  Kontalk pyserver2
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

import os, socket, time
from Queue import Queue

from twisted.application import internet, service
from twisted.internet.defer import Deferred

# local imports
from broker_twisted import *
import version
import kontalk.config as config
from kontalklib import database, utils, token, txprotobuf
from txrdq import ResizableDispatchQueue


class C2SChannel:
    '''Client channel implementation.'''

    userid = None

    def __init__(self, protocol, broker):
        self.protocol = protocol
        self.broker = broker

    def connected(self):
        # TODO
        print "connected!"

    def disconnected(self):
        print "disconnected."
        if self.userid:
            self.broker.unregister_user_queue(self.userid)

    def authenticate(self, tx_id, auth_token):
        '''Client tried to authenticate.'''
        print "[%s] authenticating token: %s" % (tx_id, auth_token)
        userid = token.verify_user_token(auth_token, self.broker.db.servers(), config.config['server']['fingerprint'])
        if userid:
            print "[%s] user %s logged in." % (tx_id, userid)
            self.userid = userid
            self.broker.register_user_queue(userid, self._incoming)
            return True

        return False

    def post_message(self, tx_id, recipient = None, mime = None, flags = None, content = None):
        '''User posted a message.'''
        # TODO
        print "[%s] posting message for: %s (mime=%s, flags=%s)" % \
            (tx_id, str(recipient), mime, str(flags))
        # TODO
        for rcpt in recipient:
            self.broker.publish_user(rcpt, [mime, flags, content])

    def _incoming(self, data):
        '''Internal queue worker.'''
        # TODO
        print "incoming message:", data
        a = NewMessage()
        a.message_id = 'TEST'
        a.sender = 'SENDER';
        a.mime = 'text/plain'
        a.encrypted = False;
        a.content = 'AOOAOAOAOAO'
        self.protocol.sendBox(a)


class S2SChannel:
    '''Server channel implementation.'''
    # TODO
    # TODO
    # TODO

    fingerprint = None

    def __init__(self, protocol, broker):
        self.protocol = protocol
        self.broker = broker

    def connected(self):
        # TODO
        print "connected!"

    def disconnected(self):
        print "disconnected."
        if self.fingerprint:
            self.broker.unregister_server_queue(self.fingerprint)

    """
    TODO
    def handshake(self, tx_id, auth_token):
        print "authenticating token: %s" % auth_token
        userid = token.verify_user_token(auth_token, self.broker.db.servers(), config.config['server']['fingerprint'])
        if userid:
            print "user %s logged in." % userid
            self.userid = userid
            self.broker.register_user_queue(userid, self._incoming)
            return True

        return False
    """

    def _incoming(self, data):
        # TODO
        print "incoming message:", data


class MessageBroker:
    '''Message broker connection manager.'''

    '''Map of the queues.'''
    _queues = {}
    '''Map of the queue routes.'''
    _routes = {}

    def __init__(self, application):
        self.application = application

    def setup(self):
        # estabilish a connection to the database
        self.db = database.connect_config(config.config)
        self.servers = self.db.servers()

        # create listening service for clients
        factory = InternalServerFactory(C2SServerProtocol, C2SChannel, self)
        service = internet.TCPServer(port=config.config['server']['c2s.bind'][1],
            factory=factory, interface=config.config['server']['c2s.bind'][0])
        service.setServiceParent(self.application)

        # create listening service for servers
        factory = InternalServerFactory(S2SServerProtocol, S2SChannel, self)
        service = internet.TCPServer(port=config.config['server']['s2s.bind'][1],
            factory=factory, interface=config.config['server']['s2s.bind'][0])
        service.setServiceParent(self.application)

    def _setup_user_queue(self, uhash):
        if uhash not in self._queues:
            self._queues[uhash] = {'spool' : Queue() }

    def register_user_queue(self, userid, worker):
        uhash, resource = userid[:utils.USERID_LENGTH], \
            userid[utils.USERID_LENGTH_RESOURCE-utils.USERID_LENGTH:]

        try:
            # stop previous queue if any
            self._queues[uhash][resource].stop()
        except:
            pass

        self._setup_user_queue(uhash)

        q = ResizableDispatchQueue(worker)
        self._queues[uhash][resource] = q
        q.start(5)

    def unregister_user_queue(self, userid):
        uhash, resource = userid[:utils.USERID_LENGTH], \
            userid[utils.USERID_LENGTH_RESOURCE-utils.USERID_LENGTH:]

        try:
            # stop previous queue if any
            self._queues[uhash][resource].stop()
            del self._queues[uhash][resource]
        except:
            pass

    """
    def register_server_queue(self, fingerprint, worker):
        self.register_queue('s:' + fingerprint, worker)

    def unregister_server_queue(self, fingerprint):
        self.unregister_queue('s:' + fingerprint)
    """

    def publish_user(self, userid, msg):
        '''Publish a message to a user, either generic or specific.'''

        if len(userid) == utils.USERID_LENGTH:
            uhash, resource = userid, None
        elif len(userid) == utils.USERID_LENGTH_RESOURCE:
            uhash, resource = userid[:utils.USERID_LENGTH], \
                userid[utils.USERID_LENGTH_RESOURCE-utils.USERID_LENGTH:]
        else:
            print "invalid userid format: %s" % userid
            # TODO should we throw an exception here?
            return None

        # specific userid
        if resource:
            self._setup_user_queue(uhash)

            if resource in self._queues[uhash][resource]:
                self._queues[uhash][resource].put(msg)

        # generic userid
        else:
            self._setup_user_queue(uhash)
            if len(self._queues[uhash]) > 1:
                for k, v in self._queues[uhash].iteritems():
                    if k != 'spool':
                        v.put(msg)
            else:
                self._queues[uhash]['spool'].put(msg)

        # TODO store on disk
