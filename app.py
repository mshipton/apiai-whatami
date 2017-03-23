#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os
import random

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)

pound = u'\u00A3'

animals = {
    'dog': {
        'covering': 'hair',
        'legs': 4
    }
}


class Animal(object):
    def __init__(self, name, properties):
        self.name = name
        self.properties = properties

    def checkCovering(self, input_covering):
        return input_covering == self.properties['covering']

    def finalGuess(self, input_guess):
        return input_guess == self.name

animals = []
animals.append(Animal("dog", {"covering": "hair", "legs": 4}))
animals.append(Animal("duck", {"covering": "feathers", "legs": 2}))


def findAnimal(context):
    input_name = context['parameters']['answer']
    return [animal for animal in animals if animal.name == input_name][0]


def getContext(req, input_name):
    for context in req['result']['contexts']:
        if context['name'] == input_name:
            return context
    return None


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    context = getContext(req, "whatami")

    print("Request:")
    print(json.dumps(req, indent=4))

    action = req.get("result").get("action")
    animal = findAnimal(context) if action != "start" else None

    if action == "start":
        res = processStart(req)
    elif action == "covering":
        res = processCovering(req, animal)        
    else:
        return

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def processStart(req):
    text = "I'm am animal, guess what I am!"
    animal = random.choice(animals)
    contextOut = {"name":"whatami", "lifespan":3, "parameters":{"answer": animal.name}}
    return makeSpeechResponse(text, contextOut)

def processCovering(req, animal):
    covering = req.get("result").get("parameters").get("covering")
    is_correct = animal.checkCovering(covering)      
    if is_correct:
        text = "I am covered in " + covering
    else:
        text = "I am not covered in " + covering
    return makeSpeechResponse(text)

def makeContextResponse(contextOut=[]):
    return {
        "contextOut": contextOut,
        "source": "apiai-webhook"
    }

def makeSpeechResponse(speech, contextOut=[]):
    return {
        "speech": speech,
        "displayText": speech,
        "contextOut": contextOut,
        "source": "apiai-webhook"
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
