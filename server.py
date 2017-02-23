import os
import json
import sys
import requests
from flask import Flask, redirect, render_template, request, url_for, Response
from slackclient import SlackClient
import random
import re

app = Flask(__name__)

APP_SECRET = os.environ['appSecret']
VALIDATION_TOKEN = os.environ['validationToken']
PAGE_ACCESS_TOKEN = os.environ['pageAccessToken']
SERVER_URL = os.environ['serverURL']
SLACK_TOKEN = os.environ.get('SLACK_TOKEN', None)
SLACK_WEBHOOK_SECRET = os.environ.get('SLACK_WEBHOOK_SECRET')

slack_client = SlackClient(SLACK_TOKEN)

ASK_OLIN = 'C4754C6JU'

f_emojis = open('emojis.txt')
emojis = f_emojis.readlines()
emojis = list(map(lambda n: n.strip(), emojis))
f_emojis.close()

f_adj = open('adjectives.txt')
adj = f_adj.readlines()
adj = list(map(lambda n: n.strip(), adj))
f_adj.close()

sender_names = {}

@app.route('/slack', methods=['POST'])
def inbound():
    if request.form.get('token') == SLACK_WEBHOOK_SECRET:
        channel = request.form.get('channel_name')
        username = request.form.get('user_name')
        text = request.form.get('text')

        #Do something with the message here
        inbound_message = "{} in {} says: {}".format(username, channel, text)
        print(inbound_message)
        send_reply(text)

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
                    
                    if sender_id not in sender_names:
                        name = generate_name()
                        sender_names[sender_id] = name

                    name = sender_names[sender_id]

                    if 'text' in messaging_event["message"]:
                        message_text = messaging_event["message"]["text"]  # the message's text

                        send_slack_message(ASK_OLIN, name, message_text)

                        send_message(sender_id, "Sent to Oliners! You'll hear back soon!")

                    else:
                        print(messaging_event["message"]["attachments"])
                        send_message(sender_id, "You sent an attachment. Can't read that")

    return "ok", 200

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

def send_slack_message(channel_id, name, message):
    slack_client.api_call(
        "chat.postMessage",
        channel=channel_id,
        text=message,
        username=name,
        attachments=[{"image_url":"http://i.ytimg.com/vi/tntOCGkgt98/maxresdefault.jpg", "title":"test"}],
        icon_emoji=":{}:".format(name[name.index('-')+1:])
    )

def generate_name():
    emoji_index = int(random.random() * len(emojis))
    adj_index = int(random.random() * len(adj))
    name = "{}-{}".format(adj[adj_index], emojis[emoji_index])
    if name in sender_names:
        return generate_name()
    else:
        return name

def send_reply(slack_message):
    # assuming in form '>name: messsage here'
    if slack_message[0:1] == '@':
        name = re.sub("[^a-zA-Z-]+", "", slack_message[1:slack_message.index(' ')])
        if name in sender_names.values():
            sender_id = list(sender_names.keys())[list(sender_names.values()).index(name)]
            send_message(sender_id, slack_message[slack_message.index(' ')+1:])
        else:
            #tell slack wrong name
            pass
    else:
        #tell slack invalid message format
        pass

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)), host=os.environ.get("HOST", '127.0.0.1'))
