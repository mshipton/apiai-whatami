#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os
import requests

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)

pound = u'\u00A3'

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    action = req.get("result").get("action")
    if action == "whatAmICovering":
        res = processWhatAmICoveringRequest(req)        
    else:
        return

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def processWhatAmICoveringRequest(req):
    text = "I am covered in " + req.get("result").get("parameters").get("covering")
    return makeSpeechResponse(text)


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
