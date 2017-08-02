import httplib2
import os
import sys
import xml.etree.ElementTree as ET

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the {{ Cloud Console }}
{{ https://cloud.google.com/console }}

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

# The amount of characters to remove from the start of the youtube URL
# Example:
# https://www.youtube.com/feeds/videos.xml?channel_id=UCfQDD-pbllOCXHYwiXxjJxA
# minus the default of 52, leaves us with just the chanel id 
# UCfQDD-pbllOCXHYwiXxjJxA
START_OF_CHANNEL_ID = 52

def get_authenticated_service(args):
  flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
    scope=YOUTUBE_READ_WRITE_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, args)

  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    http=credentials.authorize(httplib2.Http()))


# This method calls the API's youtube.subscriptions.insert method to add a
# subscription to the specified channel.
def add_subscription(youtube, channel_id):
  add_subscription_response = youtube.subscriptions().insert(
    part='snippet',
    body=dict(
      snippet=dict(
        resourceId=dict(
          channelId=channel_id
        )
      )
    )).execute()

  return add_subscription_response["snippet"]["title"]

if __name__ == "__main__":
  argparser.add_argument('--xml', help='The full path to the XML file containing the subscriptions',
  default='subscriptions.xml')
  args = argparser.parse_args()

  youtube = get_authenticated_service(args)

  # Parse the channel id's from the xml file
  xmldoc = ET.parse(args.xml)
  start = xmldoc.getroot()[0][0]

  channel_ids = []
  for child in start:
    channel_ids.append(child.get('xmlUrl')[START_OF_CHANNEL_ID:])
  
  add_subscription(youtube, 'test')

  # We have all channel ids, lets subscribe now
  for channel_id in channel_ids:
    try:
      channel_title = add_subscription(youtube, channel_id)
    except HttpError as e:
      print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
    else:
      print("A subscription to '%s' was added." % channel_title)    
