# ask.olin
### Anne LoVerso and Matthew Beaudouin-Lafon

Chatbot for prospies! Messages they send to the ask.olin Facebook chatbot are redirected to the askolin slack channel. Each prospie is given a randomly generated pseudonym to which students can respond with an @ mention or by starting a thread.​

## Details

ask.olin is built with Flask, MongoDB (pymongo for Python integration), SlackClient (Slack's API python integration) and Facebook's Messenger API (more info on specific tutorials we used can found below). It is hosted on Heroku. 

To set up this project, clone this repository and push it to Heroku. Setup a Mongo database and set the mongo_uri as an environment variable. Set up an [outgoing webhook through Slack](https://api.slack.com/outgoing-webhooks) and [create a Facebook App](https://developers.facebook.com/docs/messenger-platform/guides/quick-start) (only administrators of the page will be able to use the app unless you publish it). Set the [Slack API](https://api.slack.com/docs/oauth-test-tokens) and Messenger API tokens as environment variables on the server. Heroku should run server.py which will route messages between services!

## Acknowledged sources

Lists of animals were curated from [this animal name list](https://github.com/hzlzh/Domain-Name-List/blob/master/Animal-words.txt)

Lists of adjectives were borrowed from [docker name generator](https://github.com/docker/docker/blob/master/pkg/namesgenerator/names-generator.go) and then curated for length and added to by select words from [1-syllable adjectives](https://github.com/Sam-Izdat/kee/tree/master/words)

Figuring out how to use the syntax for Facebook Messenger with Python and Flask were helped by [this Git repo tutorial](https://github.com/hartleybrody/fb-messenger-bot)

Learning how to use Slack integrated with Flask from [this tutorial](https://realpython.com/blog/python/getting-started-with-the-slack-api-using-python-and-flask)

Learned how to setup the Messenger API through [this tutorial](https://developers.facebook.com/docs/messenger-platform/guides/quick-start).

## License
MIT License

Copyright (c) 2017 Anne LoVerso and Matthew Beaudouin-Lafon

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.