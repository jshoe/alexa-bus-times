from __future__ import print_function
import urllib2
import xml.etree.ElementTree as etree
from datetime import datetime as dt

# New imports
import codecs
import json
import os
import re
import time
 
def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
 
    try:
        # print(event['session'])
        if event['session']['new']:
            on_session_started({'requestId': event['request']['requestId']},
                               event['session'])
     
        if event['request']['type'] == "LaunchRequest":
            return on_launch(event['request'], event['session'])
        elif event['request']['type'] == "IntentRequest":
            return on_intent(event['request'], event['session'])
        elif event['request']['type'] == "SessionEndedRequest":
            return on_session_ended(event['request'], event['session'])
    except KeyError:
        pass
 
 
def on_session_started(session_started_request, session):
    """ Called when the session starts """
 
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])
 
 
def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """
 
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()
 
 
def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
 
    # Dispatch to your skill's intent handlers
    if intent_name == "GetBusTime":
        return get_bus_time(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    else:
        raise ValueError("Invalid intent")
 
 
def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
 
    Is not called when the skill returns should_end_session=true
    """
    # add cleanup logic here
 
# --------------- Functions that control the skill's behavior ------------------
 
def stop_data_fetch(bus_name, stop_num):
    """Fetch NextBus data for the line and stop number."""
    utf_decoder = codecs.getreader("utf-8")
    api_response = urllib2.urlopen('http://restbus.info/api/agencies/actransit/routes/' + bus_name + '/stops/' + str(stop_num) + '/predictions')
    data = json.load(utf_decoder(api_response))
    return data

def prediction_extract(data):
    """Extract the next three prediction times from the JSON data."""
    next_times = []
    for p in data[0]['values']:
        if len(next_times) >= 2:
            break
        next_times.append(p['minutes'])
    return next_times

def speech_format(next_times):
    """Format the next time predictions prettily."""
    line = ""
    for t in next_times:
        line += (str(t) + ", ")
    line += " minutes."
    line = re.sub(', ([0-9]+),  ', ', and \g<1> ', line) # Fix up extra commas.
    return line

def get_bus_time(intent, session):
    """ Grabs our bus times and creates a reply for the user
    """
 
    card_title = intent['name']
    session_attributes = {}
    should_end_session = True
 
    data_1 = speech_format(prediction_extract(stop_data_fetch('BUS 1', '[YOUR STOP NUMBER HERE]')))
    data_2 = speech_format(prediction_extract(stop_data_fetch('BUS 2', '[YOUR STOP NUMBER HERE]')))

    count = 1
    if count != 0:
        speech_output = "Bus 1 in " + data_1
        speech_output += " Bus 2 in " + data_2
        reprompt_text = ""
    else:
        speech_output = "Please ask me for bus times by saying, " \
                        "What are my bus times?"
        reprompt_text = "Please ask me for bus times by saying, " \
                        "What are my bus times?"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    data_1 = speech_format(prediction_extract(stop_data_fetch('BUS 1', '[YOUR STOP NUMBER HERE]')))
    data_2 = speech_format(prediction_extract(stop_data_fetch('BUS 2', '[YOUR STOP NUMBER HERE]')))
    
    response =  "We have Bus 1 in " + data_1 + " And Bus 2 in " + data_2
    speech_output = response
    reprompt_text = response
 
    session_attributes = {}
    card_title = "Bus Times"
    should_end_session = True
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# --------------- Helpers that build all of the responses ----------------------
 
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': 'SessionSpeechlet - ' + title,
            'content': 'SessionSpeechlet - ' + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }
 
def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

