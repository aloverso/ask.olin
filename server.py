import os
import json
import sys
import requests
from flask import Flask, redirect, render_template, request, url_for, Response
from slackclient import SlackClient
import random
import re
import time
from pymongo import MongoClient

app = Flask(__name__)

APP_SECRET = os.environ['appSecret']
VALIDATION_TOKEN = os.environ['validationToken']
PAGE_ACCESS_TOKEN = os.environ['pageAccessToken']
SERVER_URL = os.environ['serverURL']
SLACK_TOKEN = os.environ.get('SLACK_TOKEN', None)
SLACK_WEBHOOK_SECRET = os.environ.get('SLACK_WEBHOOK_SECRET')
MONGO_URI = os.environ['mongo_uri']

slack_client = SlackClient(SLACK_TOKEN)

ASK_OLIN = 'C4754C6JU'

client = MongoClient(MONGO_URI)
db = client.askolin
users = db.users


class User:
    def __init__(self, sender_id, name):
        self.sender_id = sender_id
        self.name = name
        self.birthday = int(time.time())
        self.last_message_sent = int(time.time())
        self.last_message_recieved = None

@app.route('/slack', methods=['POST'])
def inbound():
    if request.form.get('token') == SLACK_WEBHOOK_SECRET:
        channel = request.form.get('channel_name')
        username = request.form.get('user_name')
        text = request.form.get('text')
        timestamp = request.form.get('timestamp', None)

        print(type(request.form))
        print(request.form)

        #Do something with the message here
        inbound_message = "{} in {} says: {}".format(username, channel, text)
        print(inbound_message)
        send_reply(text, timestamp)

    return Response(), 200

@app.route('/')
def home():
    return 'ok'

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VALIDATION_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200

@app.route('/webhook', methods=['POST'])
def posthook():

    data = request.get_json()

    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    
                    name = generate_or_find_user(sender_id)

                    if 'text' in messaging_event["message"]:
                        message_text = messaging_event["message"]["text"]  # the message's text

                        send_slack_message(ASK_OLIN, name, message_text, '')

                        send_message(sender_id, "Sent to Oliners! You'll hear back soon!")

                    elif 'attachments' in messaging_event["message"]:
                        attachment_url = messaging_event["message"]["attachments"][0]["payload"]["url"]
                        send_slack_message(ASK_OLIN, name, '', attachment_url)

                        send_message(sender_id, "Sent to Oliners! You'll hear back soon!")

                    else:
                        send_message(sender_id, "Sorry, I can't read that message format!")

    return "ok", 200

# From: https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
def levenshtein(seq1, seq2):
    oneago = None
    thisrow = list(range(1, len(seq2) + 1)) + [0]
    for x in range(len(seq1)):
        twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
        for y in range(len(seq2)):
            delcost = oneago[y] + 1
            addcost = thisrow[y - 1] + 1
            subcost = oneago[y - 1] + (seq1[x] != seq2[y])
            thisrow[y] = min(delcost, addcost, subcost)
    return thisrow[len(seq2) - 1]

def send_message(recipient_id, message_text):
    params = { "access_token": PAGE_ACCESS_TOKEN }
    headers = { "Content-Type": "application/json" }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code, r.text)

def list_channels():
    channels_call = slack_client.api_call("channels.list")
    if channels_call['ok']:
        return channels_call['channels']
    return None


def channel_info(channel_id):
    channel_info = slack_client.api_call("channels.info", channel=channel_id)
    if channel_info:
        return channel_info['channel']
    return None

def send_slack_message(channel_id, name, message, attachment_url):
    slack_client.api_call(
        "chat.postMessage",
        channel=channel_id,
        text=message,
        username=name,
        attachments=[{"image_url":attachment_url, "title":""}],
        icon_emoji=":{}:".format(name[name.index('-')+1:])
    )

def send_slack_autocorrect(channel_id, autocorrected):
    pass

def autocorrect_name(given_name):
    possible_names = [('', 4)]

    for name in [user['name'] for user in users.find()]:
        lev_dist = levenshtein(name, given_name)

        if lev_dist <= 3:
            possible_names.append((name, lev_dist))

    return min(possible_names, key=(lambda x: x[1]))[0]

def generate_or_find_user(sender_id):
    if users.find_one({"sender_id":sender_id}) == None:

        f = open('names.txt')
        names = f.readlines()
        names = list(map(lambda n: n.strip(), names))
        f.close()

        new_name = names[users.count()]

        new_user = User(sender_id, new_name)

        users.insert_one(new_user.__dict__)

    return users.find_one({"sender_id":sender_id})['name']

def send_reply(slack_message, timestamp):
    # assuming in form '@name: messsage here'
    if slack_message[0:1] == '@':
        name = re.sub("[^a-zA-Z-]+", "", slack_message[1:slack_message.index(' ')])

        user = users.find_one({"name":name})
        # print("Name: {}, User: {}".format(str(name), str(user)))

        if user != None:
            sender_id = user['sender_id']
            send_message(sender_id, slack_message[slack_message.index(' ')+1:])
        else:
            print("Can't find the name")
            best_guess = autocorrect_name(name)
            if best_guess != '':
                user = users.find_one({"name":best_guess})
                # print("best_guess: {}, user: {}".format(str(best_guess), str(user)))
                sender_id = user['sender_id']
                print('Did you mean: {}'.format(best_guess))
                send_message(sender_id, slack_message[slack_message.index(' ')+1:])
                # send_slack_autocorrect(sender_id, slack_message[slack_message.index(' ')+1:])

    else:
        print("Doesn't start with @, checking to see if it's in a thread")

        thread_messages = slack_client.api_call(
            "channels.history",
            channel=ASK_OLIN,
            latest=timestamp,
            inclusive=True,
            count=1
        )

        print("Thread Messages")
        print(thread_messages)

        thread_message = thread_messages['messages'][0]

        # Check if poster is involved in a thread
        if thread_message.get('thread_ts', None) != None:
            if thread_message.get('replies', None) == None:     # No replies -> Not parent
                parent_messages = slack_client.api_call(
                    "channels.history",
                    channel=ASK_OLIN,
                    latest=thread_message.get('thread_ts', None),
                    inclusive=True,
                    count=1
                )
                print("Parent Messages")
                print(parent_messages)
                # print('Thread debug: Parent message = "{}"'.format(parent_message['text']))

                message = parent_messages['messages'][0]

            else:                                               # Has replies -> Must be the parent
                message = thread_message

            # Check that the parent is a bot
            if message.get('subtype', None) == 'bot_message':
                user = users.find_one({"name" : thread_message['username']})
                print("username = {}, user = {}".format(thread_message['username'], user))

                if user != None:
                    sender_id = user['sender_id']
                    send_message(sender_id, slack_message)
                else:
                    print("Thread '{}' not found".format(thread_ts))
    

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)), host=os.environ.get("HOST", '127.0.0.1'))
