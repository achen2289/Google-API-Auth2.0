import requests
import urllib
import json
from subprocess import Popen

'''
Original source code from @shin1ogawa, @ymotongpoo,
written in Python2 and Java
Makes an API call to gain authorization from Google to 
read an authenticated user's G-cal
Retrieves one time access token but not refresh token

https://gist.github.com/1899391
https://gist.github.com/ymotongpoo/1907281

Adapted to use authorization to make a call Gmail
watch() API call on a mailbox to set up push notifications
Supports Python3

More information is available at
  - https://developers.google.com/gmail/api/v1/reference/users/watch
  - https://developers.google.com/gmail/api/guides/push
'''

# replace with OAuth 2.0 credentials of your application
client_id = ""
client_secret = ""
redirect_uri = ""
base_url = r"https://accounts.google.com/o/oauth2/"
authorization_code = ""
access_token = ""

'''
Retrieve authorization_code from authorization API
'''
def retrieve_authorization_code():
  authorization_code_req = {
    "response_type": "code",
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "scope": (r"https://www.googleapis.com/auth/gmail.readonly")
    }

  # this implementation requires user to retrieve the authorization code
  # web server access would bypass this as dealt with through server
  r = requests.get(base_url + "auth?%s" % urllib.parse.urlencode(authorization_code_req),
                   allow_redirects=False)
  url = r.headers.get('location')
  Popen(["open", url])

  authorization_code = input("\nAuthorization Code >>> ")
  return authorization_code

'''
Retrieve access_token and refresh_token from Token API
'''
def retrieve_tokens(authorization_code):
  access_token_req = {
    "code" : authorization_code,
    "client_id" : client_id,
    "client_secret" : client_secret,
    "redirect_uri" : redirect_uri,
    "grant_type": "authorization_code",
    }
  content_length=len(urllib.parse.urlencode(access_token_req))
  access_token_req['content-length'] = str(content_length)

  r = requests.post(base_url + "token", data=access_token_req)
  data = json.loads(r.text)
  return data

'''
Make watch API call with proper authorization and access_token
'''
def call_watch(auth_code = None):
  global authorization_code
  if auth_code == None:
    authorization_code = retrieve_authorization_code()
  else:
    authorization_code = auth_code
  tokens = retrieve_tokens(authorization_code)
  access_token = tokens['access_token']
  authorization_header = {"Authorization": "OAuth %s" % access_token}

  user_id = 'me'
  watch_endpoint = 'https://www.googleapis.com/gmail/v1/users/' + user_id + '/watch'

  label_ids = ['INBOX']
  labelFilterAction = 'include'
  topic_name = 'projects/delivery-consolidation-277305/topics/food-deliveries'

  request = {}
  request['labelIds'] = label_ids
  request['labelFilterAction'] = labelFilterAction
  request['topicName'] = topic_name

  r = requests.post(url=watch_endpoint, headers=authorization_header, data=request)
  r_json = json.loads(r.text)
  history_id = r_json['historyId']

  file = open('start_history_id.txt', 'w+')
  file.write(history_id) # save current history id
  file.close()

  print (history_id)
  return

if __name__ == '__main__':
  call_watch()