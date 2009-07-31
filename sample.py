'''
Sample app to test xmpp extensions to fireeagle python library
'''
import pyrostream, ConfigParser

def callback(conn, msg):
  print "client_callback:"
  print msg

config = ConfigParser.ConfigParser()
config.readfp(open('sample.cfg'))

fe_client = pyrostream.FireEagleXmppClient( config.get('FireEagle','pubsub.server'),  # FireEagle pubsub server
                                            config.get('Jabber','jid'),               # JID (intermediate server)
                                            config.get('Jabber','password'),          # password (auth above JID)
                                            config.get('FireEagle','oauth.consumer_key'),     # FireEagle consumer key
                                            config.get('FireEagle','oauth.consumer_secret'))  # FireEagle consumer secret
print "making ping request"
print fe_client.ping()

print "making discovery request"
print fe_client.disco()

#print "adding fireeagle to your roster"
#fe_client.roster_add_fireeagle()

print "making subscribe request"
print fe_client.subscribe(config.get('Token','oauth.token'), config.get('Token','oauth.token_secret'))

print "checking subscriptions"
print fe_client.subscriptions(config.get('GeneralPurposeToken','oauth.token'), config.get('GeneralPurposeToken','oauth.token_secret'))

#print "making unsubscribe request"
#print fe_client.unsubscribe(config.get('Token','oauth.token'), config.get('Token','oauth.token_secret'))

print "listening to location stream"
# supported events FESTREAM_ALL, FESTREAM_LOCATION_UPDATE
fe_client.register_callback(callback)
fe_client.run()
