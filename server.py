import os
import json
import sys
import requests
from flask import Flask, redirect, render_template, request, url_for
from slackclient import SlackClient

app = Flask(__name__)

APP_SECRET = os.environ['appSecret']
VALIDATION_TOKEN = os.environ['validationToken']
PAGE_ACCESS_TOKEN = os.environ['pageAccessToken']
SERVER_URL = os.environ['serverURL']
SLACK_TOKEN = os.environ.get('SLACK_TOKEN', None)
SLACK_WEBHOOK_SECRET = os.environ.get('SLACK_WEBHOOK_SECRET')

slack_client = SlackClient(SLACK_TOKEN)

ASK_OLIN = 'C4754C6JU'

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

def send_slack_message(channel_id, message):
    slack_client.api_call(
        "chat.postMessage",
        channel=channel_id,
        text=message,
        username='pythonbot',
        icon_emoji=':robot_face:'
    )

@app.route('/slack', methods=['POST'])
def inbound():
    if request.form.get('token') == SLACK_WEBHOOK_SECRET:
        channel = request.form.get('channel_name')
        username = request.form.get('user_name')
        text = request.form.get('text')

        #Do something with the message here
        inbound_message = username + " in " + channel + " says: " + text
        print(inbound_message)

    return Response(), 200

@app.route('/', methods=['GET'])
def test():
    return Response('It works!')

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
                    
                    if 'text' in messaging_event["message"]:
                        message_text = messaging_event["message"]["text"]  # the message's text

                        send_slack_message(ASK_OLIN, message_text)

                        send_message(sender_id, "I got: " + message_text)

                    else:
                        send_message(sender_id, "You sent an attachment. Can't read that")

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

                else:
                    pass

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


if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)), host=os.environ.get("HOST", '127.0.0.1'))
