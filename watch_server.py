import requests
import urllib
import json
from subprocess import Popen

import extract_email

'''
Original source code from @shin1ogawa, @ymotongpoo,
written in Python2 and Java.
Makes an API call to gain authorization from Google to 
read an authenticated user's G-cal.

https://gist.github.com/1899391
https://gist.github.com/ymotongpoo/1907281

Adapted to use authorization to make a call Gmail watch() API 
call on a mailbox to set up push notifications.
Implemented this script for offline user authorization and
web application usage.
Requires prior creation of Google Pub/Sub topic (and subscriber)
Supports Python3

More information is available at
    - https://developers.google.com/gmail/api/v1/reference/users/watch
    - https://developers.google.com/gmail/api/guides/push
    - https://developers.google.com/gmail/api/auth/web-server
    - https://developers.google.com/identity/protocols/oauth2/web-server#httprest_3
'''

__author___ = "@achen2289"

# replace with OAuth 2.0 credentials of your application
client_id = ""
client_secret = ""
redirect_uri = ""
base_url = r"https://accounts.google.com/o/oauth2/"
authorization_code = ""
access_token = ""

# Retrieve authorization_code from authorization API
# Once a refresh_token is created, authorization_code is no longer needed
def retrieve_authorization_code(offline_access = True):
    authorization_code_req = {
        "client_id" : client_id,
        "redirect_uri" : redirect_uri,
        "access_type" : "offline",
        "prompt" : "consent",
        "response_type" : "code",
        "scope" : (r"https://www.googleapis.com/auth/gmail.readonly")
        }

    # user authentication is required to retrieve the authorization code
    r = requests.get(base_url + "auth?%s" % urllib.parse.urlencode(authorization_code_req),
                                     allow_redirects=False)
    url = r.headers.get('location')
    Popen(["open", url])

    authorization_code = input("\nAuthorization Code >>> ") # determine from redirect uri
    return authorization_code

# Retrieve access_token and refresh_token from Token API
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

# Get new_access_token from refresh_token
def new_access_token(refresh_token):
    refresh_token_req = {
        "client_id" : client_id,
        "client_secret" : client_secret,
        "grant_type" : "refresh_token",
        "refresh_token" : refresh_token
    }

    r = requests.post(base_url + "token", data=refresh_token_req)
    data = json.loads(r.text)
    new_access_token = data['access_token']
    print ("New access token generated!")
    return new_access_token

# Link together authorization and authentication steps
# Write codes and tokens to files in directory for simplicity
def main():
    global authorization_code
    try: # get authorization_code in case access_token must be created
        with open('auth_code.txt', 'r') as f:
            authorization_code = f.readlines()[0]
    except FileNotFoundError:
        authorization_code = retrieve_authorization_code()
        with open('auth_code.txt', 'w+') as f:
            f.write(authorization_code)

    # get access token, or create one if have not yet
    try:
        with open('access_token.txt', 'r') as f:
            access_token = f.readlines()[0]
        with open('refresh_token.txt', 'r') as f:
            refresh_token = f.readlines()[0]
    # create access_token and refresh_token if no access_token exists
    except FileNotFoundError:
        tokens = retrieve_tokens(authorization_code)
        access_token = tokens['access_token']
        with open('access_token.txt', 'w+') as f:
            f.write(access_token)
        refresh_token = tokens['refresh_token']
        with open('refresh_token.txt', 'w+') as f:
            f.write(refresh_token)

    call_watch(refresh_token)

# Make watch API call with proper authorization and access_token/refresh_token
# Watch call output of historyId is stored in start_history_id.txt
def call_watch(refresh_token):
    access_token = new_access_token(refresh_token) # ensure that the token has not expired
    authorization_header = {"Authorization": "OAuth %s" % access_token}

    user_id = 'me'
    watch_endpoint = 'https://www.googleapis.com/gmail/v1/users/' + user_id + '/watch'

    label_ids = ['INBOX']
    labelFilterAction = 'include'
    topic_name = '' # insert name of Google Pub/Sub topic

    request = {}
    request['labelIds'] = label_ids
    request['labelFilterAction'] = labelFilterAction
    request['topicName'] = topic_name

    r = requests.post(url=watch_endpoint, headers=authorization_header, data=request)
    r_json = json.loads(r.text)
    history_id = r_json['historyId'] # historyId of current mailbox sequence

    f = open('start_history_id.txt', 'w+')
    if len(f.readlines()) != 0:
        f.close()
        extract_email.fetchMail(history_id) # flush out any emails that need to be processed
    else:
        f.write(history_id) # save current history id to file
        f.close()

    print (history_id)
    return

if __name__ == '__main__':
    main()
