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
import logging
import argparse

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', help="Be verbose", action="store_true",
                    dest="verbose")
args = parser.parse_args()
logging.basicConfig(level=logging.DEBUG if args.verbose else logging.DEBUG)
logger = logging.getLogger(__name__)


class Animal(object):
    def __init__(self, name, properties):
        self.name = name
        self.properties = properties

    def checkCovering(self, input_covering):
        return input_covering == self.properties['covering']

    def checkPlace(self, input_place):
        return input_place in self.properties['places']

    def checkLegs(self, input_legs):
        return input_legs == self.properties['legs']

    def checkGuess(self, input_guess):
        return input_guess == self.name

    def getHint(self):
        return random.choice(self.properties['hints'])

import json

with open("animals.json", "r") as f:
    data = json.load(f)[0]
    animals = [Animal(key, value) for key, value in data.items()]

def findAnimal(context):
    logger.debug("Finding animal...")
    input_name = context['parameters']['answer']
    return [animal for animal in animals if animal.name == input_name][0]


def getContext(req, input_name):
    logger.debug("Getting context")
    for context in req['result']['contexts']:
        if context['name'] == input_name:
            return context
    return None


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    context = getContext(req, "whatami")
    logger.debug("Context received")

    # logger.debug("Request:")
    # logger.debug(json.dumps(req, indent=4))

    action = req.get("result").get("action")
    logger.debug("Action = {}".format(action))
    animal = findAnimal(context) if action != "start" and action != "restart" else None
    logger.debug("Animal = {}".format(animal))

    if action == "start" or action == "restart":
        res = processStart(req)
    elif action == "covering":
        res = processCovering(req, animal)
    elif action == "guessPlace":
        res = processGuessPlace(req, animal)                
    elif action == "legs":
        res = processLegs(req, animal)
    elif action == "guessAnswer":
        res = processGuessAnswer(req, animal)
    elif action == "hint":
        res = processHint(req, animal)
    else:
        logger.warning("Unknown action")
        return None
    logger.debug("Fulfilled intents")

    res = json.dumps(res, indent=4)
    # print(res)
    logger.debug("Response json dumped")
    r = make_response(res)
    logger.debug("Making final json response")
    r.headers['Content-Type'] = 'application/json'
    return r

def processStart(req):
    text = "I'm am animal, guess what I am!"
    animal = random.choice(animals)
    logger.debug("Random animal chosen: {}".format(animal))
    contextOut = [{"name":"whatami", "lifespan":3, "parameters":{"answer": animal.name}}]
    return makeSpeechResponse(text, contextOut)

def processCovering(req, animal):
    logger.debug("Processing processCovering")
    covering = req.get("result").get("parameters").get("covering")
    logger.debug("Input covering = {}".format(covering))
    is_correct = animal.checkCovering(covering)      
    if is_correct:
        text = "I am covered in " + covering
    else:
        if len(covering) == 0:
            text = "You have to guess what I'm covered in"
        else:
            text = "I am not covered in " + covering
    return makeSpeechResponse(text)

def processGuessPlace(req, animal):
    logger.debug("Processing processGuessPlace")
    place = req.get("result").get("parameters").get("place")
    logger.debug("Input place = {}".format(place))
    is_correct = animal.checkPlace(place)      
    if is_correct:
        text = "Yes I do"
    else:
        if len(place) == 0:
            text = "You have to guess where I can be found"
        else:
            text = "No I don't"
    return makeSpeechResponse(text)    

def processLegs(req, animal):
    logger.debug("Processing processLegs")
    legs = req.get("result").get("parameters").get("legs")
    logger.debug("Input legs = {}".format(legs))
    is_correct = animal.checkLegs(int(legs)) if len(legs) > 0 else False
    if is_correct:
        text = "I do have {} legs".format(legs)
    else:
        if len(legs) == 0:
            text = "You have to guess how many legs I have"
        else:
            text = "I do not have {} legs".format(legs)
    return makeSpeechResponse(text)

def processGuessAnswer(req, animal):
    logger.debug("Processing guessAnswer")
    guess = req.get("result").get("parameters").get("guess")
    logger.debug("Guess = {}".format(guess))
    is_correct = animal.checkGuess(guess)   
    logger.debug("Guess is correct = {}".format(is_correct))   
    if is_correct:
        sound = '<audio src="https://orsilus.com/test/whatami/{}.mp3" />'.format(guess)
        text = "<speak>You're right! I am a {}!{} <break time='1s'/> Do you want to play again?</speak>".format(guess, sound)
        contextOut = [{"name":"gameover", "lifespan":1}]
    else:
        text = "No, I'm not a {} :(. Try again!".format(guess)
        contextOut = []
    return makeSpeechResponse(text, contextOut)

def processHint(req, animal):
    logger.debug("Grabbing a hint")
    hint = animal.getHint()
    logger.debug("Giving hint: {}".format(hint))
    return makeSpeechResponse(hint) 

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

    app.run(debug=args.verbose, port=port, host='0.0.0.0')
