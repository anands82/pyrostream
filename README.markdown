# pyrostream

pyrostream is an open source python library which aids development of tools for consuming FireEagle's XMPP pubsub feed.
(http://fireeagle.yahoo.net)

## REQUIREMENTS
- [xmpppy - xmpp lib for python](http://xmpppy.sourceforge.net)
- [fireeagle python binding](http://fireeagle.yahoo.net/developer/code/python)

## GETTING STARTED
1. Get fireeagle access token and secret
- [Create a New fireeagle Application](http://fireeagle.yahoo.net/developer/create)
- Select “Auth for web-based services”
- Fill in the blanks and create it
- Take note of your General Purpose Token and Secret
- Obtain an Access Token and Secret by sending a user through the [OAuth Dance](http://fireeagle.yahoo.net/developer/documentation/web_auth)
2. Create a JID on your XMPP server (if you dont have one, go to http://www.ejabberd.im)

## CODE
1. Fill in the config file
2. Initialize obj pyrostream.FireEagleXmppClient
3. Add fireeagle.com to your roster
    fe_client.add_fireeagle_to_roster()
4. Subscribe to location update stream for the access token
    fe_client.subscribe(config.get('Token','oauth.token'), config.get('Token','oauth.token_secret'))
5. check subscriptions
    fe_client.subscriptions(config.get('GeneralPurposeToken','oauth.token'), config.get('GeneralPurposeToken','oauth.token_secret'))
6. listen to location update stream
    fe_client.register_callback('FESTREAM_LOCATION_UPDATE', callback)
    fe_client.run()

## EXAMPLE
* check out sample.py

## FEEDBACK
* Please report bugs to anands82@yahoo.com
* Send feedback to [Fireeagle Yahoo Group](http://tech.groups.yahoo.com/group/fireeagle)
