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

    def getSize(self):
        return self.properties['size']

import json

with open("farm.json", "r") as f:
    data = json.load(f)
    animals = []
    for row in data:
        for key, value in row.items():
            animals.append(Animal(key, value))

def findAnimal(context):
    try:
        logger.debug("Finding animal...")
        input_name = context['parameters']['answer']
        return [animal for animal in animals if animal.name == input_name][0]
    except:
        return None

def getContext(req, input_name):
    logger.debug("Getting context")
    for context in req['result']['contexts']:
        if context['name'] == input_name:
            logger.debug("Context found! Returning context {}".format(input_name))
            return context
    logger.warning("No context found, returning None context")
    return None


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    action = req.get("result").get("action")
    logger.debug("Action = {}".format(action))

    context = getContext(req, "whatami")
    logger.debug("Context received")


    res = process_action(req, action, context)
    logger.debug("Fulfilled intents")

    res = json.dumps(res, indent=4)
    # print(res)
    logger.debug("Response json dumped")
    r = make_response(res)
    logger.debug("Making final json response")
    r.headers['Content-Type'] = 'application/json'
    return r


def process_action(req, action, context):
    animal = findAnimal(context)
    if animal is None:
        logger.debug("No animal found in context, getting new animal")
        animal = random.choice(animals)
    logger.debug("Animal = {}".format(animal.name))

    contextOut = [{"name":"whatami", "lifespan":2, "parameters":{"answer": animal.name}}]

    if action in ["start", "restart"]:
        res = processStart(req, contextOut)
    elif action == "covering":
        res = processCovering(req, animal, contextOut)
    elif action == "guessPlace":
        res = processGuessPlace(req, animal, contextOut)                
    elif action == "legs":
        res = processLegs(req, animal, contextOut)
    elif action == "guessSize":
        res = processSize(req, animal, contextOut)
    elif action == "guessAnswer":
        res = processGuessAnswer(req, animal, contextOut)
    elif action == "hint":
        res = processHint(req, animal, contextOut)
    else:
        res = makeSpeechResponse("Unknown action", contextOut)
        logger.warning("Unknown action")
        return None
    return res

def processStart(req, contextOut):
    text = ["I'm a farm animal, guess what I am!"]
    text = random.choice(text)
    return makeSpeechResponse(text, contextOut)

def processCovering(req, animal, contextOut):
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
    return makeSpeechResponse(text, contextOut)

def processGuessPlace(req, animal, contextOut):
    logger.debug("Processing processGuessPlace")
    place = req.get("result").get("parameters").get("place")
    logger.debug("Input place = {}".format(place))
    is_correct = animal.checkPlace(place)      
    if is_correct:
        text = "Yes I do"
    else:
        if len(place) == 0:
            text = "Take another guess"
        elif place == "nowhere":
            text = "You need to guess the place"
        else:
            text = "No I don't"
    return makeSpeechResponse(text, contextOut)    

def processLegs(req, animal, contextOut):
    logger.debug("Processing processLegs")
    legs = req.get("result").get("parameters").get("legs")
    logger.debug("Input legs = {}".format(legs))
    is_correct = animal.checkLegs(int(legs)) if len(legs) > 0 else False
    if is_correct:
        text = "Yes, I do have {} legs".format(legs)
    else:
        if len(legs) == 0:
            text = "You have to guess how many legs I have"
        else:
            text = "No, I do not have {} legs".format(legs)
    return makeSpeechResponse(text, contextOut)

def processGuessAnswer(req, animal, contextOut):
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
        text = "No. Try again!".format(guess)
        contextOut = []
    return makeSpeechResponse(text, contextOut)

def processSize(req, animal, contextOut):
    logger.debug("Grabbing size")
    size = animal.getSize()
    logger.debug("Size = {}".format(size))
    text = "I am {}".format(size)
    return makeSpeechResponse(text, contextOut) 

def processHint(req, animal, contextOut):
    logger.debug("Grabbing a hint")
    text = animal.getHint()
    logger.debug("Giving hint: {}".format(text))
    return makeSpeechResponse(text, contextOut) 

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
