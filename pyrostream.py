"""
Fire Eagle XMPP Python module v0.1
by Anand S <anands82@yahoo.com>

Source repo at http://github.com/anands82/pyrostream 

Example usage:
sample.py


Copyright (c) 2009, Anand S
All rights reserved.

Unless otherwise specified, redistribution and use of this software in
source and binary forms, with or without modification, are permitted
provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * The name of the author nor the names of any contributors may be
      used to endorse or promote products derived from this software without
      specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import fireeagle_api
import sys,os,xmpppy,random,time
import hmac,hashlib,binascii,urllib
from xml.dom import minidom
from pprint import pprint

# the following are all possible event types
EVENT_TYPES = ['FESTREAM_ALL', 'FESTREAM_LOCATION_UPDATE']

USER_LOCATION = 'location', {
    'best_guess'   : fireeagle_api.boolean,
    'box'          : fireeagle_api.geo_str,
    'point'        : fireeagle_api.geo_str,
    'level'        : int,
    'level_name'   : fireeagle_api.string,
    'located_at'   : fireeagle_api.date,
    'name'         : fireeagle_api.string,
    'place_id'     : fireeagle_api.string,
    'woeid'        : fireeagle_api.string,
    'query'        : fireeagle_api.string,
}

USER = 'user', {
    'token'   : fireeagle_api.string,
    'location': USER_LOCATION,
}

# url escape
def escape(s):
    # escape '/' too
    return urllib.quote(s, safe='~')

XMPP_CONN_CHECK_TIMEOUT = 1
JID_RESOURCE = 'fireeagle'

FIREEAGLE_JABBER_NODE_PREFIX = '/api/0.1/user/'
FIREEAGLE_XMPP_SERVER = 'fireeagle.com'

class FireEagleXmppException( Exception ):
  pass

# Implementation of XEP-235 (OAuth over XMPP using pubsub)
class OAuthXmpp:

  # initialize info for making xmpp requests to fireeagle pubsub server
  def __init__(self, server=FIREEAGLE_XMPP_SERVER, from_jid=None, consumer_key=None, consumer_secret=None):
    self.server = server
    self.from_jid = from_jid
    self.consumer_key = consumer_key
    self.consumer_secret = consumer_secret


  # generate string out of oauth params joining with '&'
  def __build_oauth_params_string(self, oauth_params):
    param_array = []
    for k, v in oauth_params.iteritems():
      param_array.append(k+'='+v)
    param_array.sort()
    return '&'.join(param_array)


  # generate xml string out of oauth_params
  def __build_oauth_params_xml(self, oauth_params):
    param_array = []
    for k, v in oauth_params.iteritems():
      param_array.append('<'+k+'>'+v+'</'+k+'>')
    return '<oauth xmlns="urn:xmpp:oauth:0">' + ''.join(param_array) + '</oauth>'


  # generate signature base string from oauth params
  def __build_signature_base_string(self, oauth_params):
    sig = (
            escape('iq'),
            escape(xmpppy.protocol.JID(self.from_jid).getStripped() + '&' + self.server),
            escape(self.__build_oauth_params_string(oauth_params)),
        )
    key = '%s&' % escape(self.consumer_secret)
    key += escape(self.token_secret)
    raw = '&'.join(sig)
    return key, raw


  # generate signature
  def __build_signature(self, oauth_params):
    key, raw = self.__build_signature_base_string(oauth_params)
    # hmac object
    try:
      import hashlib # 2.5
      hashed = hmac.new(key, raw, hashlib.sha1)
    except:
      import sha # deprecated
      hashed = hmac.new(key, raw, sha)
    # calculate the digest base 64
    sig = binascii.b2a_base64(hashed.digest())[:-1]
    return sig


  # builds the pubsub request
  def build_pubsub_request(self, request, token=None, secret=None):
    self.token_secret = secret
    oauth_params = {    'oauth_consumer_key'      : self.consumer_key,
                        'oauth_nonce'             : str(random.randint(1000000000,9999999999)),
                        'oauth_signature_method'  : 'HMAC-SHA1',
                        'oauth_timestamp'         : str(int(time.time())),
                        'oauth_token'             : token,
                        'oauth_version'           : '1.0'
                    }
    signature = self.__build_signature(oauth_params)
    oauth_params['oauth_signature'] = signature;
    request_str = '<pubsub xmlns="http://jabber.org/protocol/pubsub">'

    # now the oauth part
    if request == 'subscribe' or request == 'unsubscribe':
      request_str += '<' + request + ' ' + \
                      'node="' + FIREEAGLE_JABBER_NODE_PREFIX + oauth_params['oauth_token'] + '" ' + \
                      'jid="'+self.from_jid+'"/>' + \
                      self.__build_oauth_params_xml(oauth_params) 
    elif request == 'subscriptions':
      request_str += self.__build_oauth_params_xml(oauth_params) + '<'+request+'/>'
    else:
      raise FireEagleXmppException, "unknown request ", request

    request_str += '</pubsub>'
    
    return request_str
    



# FireEagle XMPP Client implementation 
class FireEagleXmppClient:

  # constructor
  def __init__(self, server=FIREEAGLE_XMPP_SERVER, jid=None, passwd=None, consumer_key=None, consumer_secret=None):
    self.fireeagle_server = server
    self.jid = jid
    self.passwd = passwd
    # init oauth
    if consumer_key!=None and consumer_secret!=None:
      self.set_consumer_key_and_secret(consumer_key, consumer_secret)
    # auth using the supplied jid and pass 
    jid = xmpppy.protocol.JID(jid)
    self.xmpp_client = xmpppy.Client(jid.getDomain(),debug=[])
    if self.xmpp_client.connect() == "":
      raise FireEagleXmppException, "cannot connect to ",jid.getDomain()      
    if self.xmpp_client.auth(jid.getNode(),passwd,JID_RESOURCE) == None:
      raise FireiEagleXmppException, "authentication failed for ",jid.getNode()

    # this will be used by blocking_return method
    self.response = ''
    # initialize the callback_hash
    self.callback_hash = {}


  # desctructor
  def __del__(self):
    self.xmpp_client.disconnect();
  

  # store message in an object variable for future use
  def __store_response(self, conn, msg):
    self.response = msg


  # build xmpp request header
  def __build_request_header(self, type):
    req_id= type+str(random.randint(100,999))
    return "type=\'" + type + "\' from=\'" + self.jid + "\' to=\'" + self.fireeagle_server + "\' id=\'" + req_id + "\'"


  # build complete xmpp request
  def __build_request_xml(self, req, type, body):
    header = self.__build_request_header(type)
    return '<' + req  + " " + header + '>' + body + '</' + req + '>'


  # construct request based on type 
  def __construct_request(self, type, pubsub_request=None, token=None, secret=None):
    req_xml = ''
    if type=='ping':
      req_xml = self.__build_request_xml('iq', 'get', '<ping xmlns=\'urn:xmpp:ping\'/>')
    elif type=='disco':
      req_xml = self.__build_request_xml('iq', 'get', '<query xmlns="http://jabber.org/protocol/disco#info"/>')
    elif type=='pubsub':
      body = self.oauth.build_pubsub_request(pubsub_request,token,secret)
      req_xml = self.__build_request_xml('iq', 'set', body)
    else: 
      raise FireEagleXmppException, "unknown request type: ",type

    return req_xml
     

  # store response and return
  def __blocking_return(self,request_string):
    self.xmpp_client.RegisterHandler('iq',self.__store_response)
    self.xmpp_client.send(request_string)
    ret_size = '0'
    while ret_size=='0':
      ret_size = self.xmpp_client.Process(XMPP_CONN_CHECK_TIMEOUT)
    self.xmpp_client.UnregisterHandler('iq',self.__store_response)
    return self.response


  # TODO do we need to support optional callbacks to ping/disco.
  #def __request_with_callback(self,request_string,callback):
  #  response_message = self.__blocking_return(request_string)
  #  if callback is not None:
  #    callback(response_message)
  #  return response_message


  # TODO error check for FESTREAM_LOCATION_UPDATE 
  # possible types: FESTREAM_ALL, FESTREAM_LOCATION_UPDATE
  def __get_event_types(self,type):
    ret_arr = ['FESTREAM_ALL']
    if(str(type) == 'http://jabber.org/protocol/pubsub#event'):
      ret_arr.append('FESTREAM_LOCATION_UPDATE')
    return ret_arr


  # callback for all xmpp messages from fireeagle
  # calls appropriate user set callbacks
  def __master_callback(self,conn,msg):
    response_dom = minidom.parseString (str(msg))
    if response_dom.documentElement.tagName != 'message':
      return

    for event in response_dom.getElementsByTagName("event"):
      type_arr = self.__get_event_types(event.attributes['xmlns'].value)

      for type in type_arr:
        if not self.callback_hash.has_key(type):
          continue

        if type == 'FESTREAM_LOCATION_UPDATE':
          element, conversions = USER
          resp = self.fireeagle.build_return(event, element, conversions)
        if type == 'FESTREAM_ALL':
          resp = event.toxml()
        
        self.callback_hash[type](conn,resp)

    response_dom.unlink()
 

  # public functions

  def roster_add_fireeagle(self):
    return self.xmpp_client.getRoster().Subscribe(self.fireeagle_server)

  # incase you didnt do it during init()
  def set_consumer_key_and_secret(self, consumer_key, consumer_secret):
    self.oauth = OAuthXmpp(self.fireeagle_server, self.jid, consumer_key, consumer_secret)
    self.fireeagle = fireeagle_api.FireEagle(self.oauth.consumer_key, self.oauth.consumer_secret)

  # ping fireeagle server  
  def ping(self):
    return self.__blocking_return(self.__construct_request('ping'))

  # disovery request to fireeagle server
  def disco(self):
    return self.__blocking_return(self.__construct_request('disco'))

  # make a subscribe request and wait for response
  # TODO: check whether subscription was successful, handle errors
  def subscribe(self, token, secret):
    request_str = self.__construct_request('pubsub','subscribe',token, secret)
    return self.__blocking_return(request_str)

  def unsubscribe(self, token, secret):
    request_str = self.__construct_request('pubsub','unsubscribe',token, secret)
    return self.__blocking_return(request_str)

  def subscriptions(self, token, secret):
    request_str = self.__construct_request('pubsub','subscriptions',token, secret)
    return self.__blocking_return(request_str)

  # register callbacks
  # supported events FESTREAM_ALL, FESTREAM_LOCATION_UPDATE
  def register_callback(self, callback, event='FESTREAM_LOCATION_UPDATE'):
    if event in EVENT_TYPES:
      self.callback_hash[event] = callback
      return True
    return False
    
  # goes on an infinite loop
  def run(self):
    self.xmpp_client.sendInitPresence()
    self.xmpp_client.RegisterHandler('message',self.__master_callback)
    while True:
      self.xmpp_client.Process(XMPP_CONN_CHECK_TIMEOUT)
