from __future__ import division
from flask import Flask, render_template
import beta
import alpha
import pickle
import re
import sys
import os.path
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import pyaudio
from six.moves import queue
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pyperclip
from subprocess import call
import psycopg2
import keyboard

app = Flask(__name__)

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
SCOPES = ['https://www.googleapis.com/auth/documents']
DOCUMENT_ID = ""

@app.route('/')
def hello():
	return render_template('index.html')

@app.route('/type')
def flaskThread():
	global DOCUMENT_ID
	creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
	if os.path.exists('token.pickle'):
	    with open('token.pickle', 'rb') as token:
	        creds = pickle.load(token)
	# If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
	    if creds and creds.expired and creds.refresh_token:
	        creds.refresh(Request())
	    else:
	        flow = InstalledAppFlow.from_client_secrets_file(
	            'credentials.json', SCOPES)
	        creds = flow.run_local_server(port=0)
	    # Save the credentials for the next run
	    with open('token.pickle', 'wb') as token:
	        pickle.dump(creds, token)

	service = build('docs', 'v1', credentials=creds)

	# print("Please open existing or create new document")

	language_code = 'en-US'  # a BCP-47 language tag

	client = speech.SpeechClient()
	config = types.RecognitionConfig(
	    encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
	    sample_rate_hertz=RATE,
	    language_code=language_code)
	streaming_config = types.StreamingRecognitionConfig(
	    config=config,
	    interim_results=False)


	with beta.MicrophoneStream(RATE, CHUNK, ) as stream:
	    audio_generator = stream.generator()
	    requests = (types.StreamingRecognizeRequest(audio_content=content)
	                for content in audio_generator)

	    responses = client.streaming_recognize(streaming_config, requests)
	    jawnson = beta.listen_print_loop(responses, service, DOCUMENT_ID, False)

	    # Now, put the transcription responses to use.
	    return render_template('type.html', text = jawnson[0])

@app.route('/cmd')
def command():
	global DOCUMENT_ID
	creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
	if os.path.exists('token.pickle'):
	    with open('token.pickle', 'rb') as token:
	        creds = pickle.load(token)
	# If there are no (valid) credentials available, let the user log in.
	if not creds or not creds.valid:
	    if creds and creds.expired and creds.refresh_token:
	        creds.refresh(Request())
	    else:
	        flow = InstalledAppFlow.from_client_secrets_file(
	            'credentials.json', SCOPES)
	        creds = flow.run_local_server(port=0)
	    # Save the credentials for the next run
	    with open('token.pickle', 'wb') as token:
	        pickle.dump(creds, token)

	service = build('docs', 'v1', credentials=creds)

	# print("Please open existing or create new document")

	language_code = 'en-US'  # a BCP-47 language tag

	client = speech.SpeechClient()
	config = types.RecognitionConfig(
	    encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
	    sample_rate_hertz=RATE,
	    language_code=language_code)
	streaming_config = types.StreamingRecognitionConfig(
	    config=config,
	    interim_results=False)


	with beta.MicrophoneStream(RATE, CHUNK, ) as stream:
	    audio_generator = stream.generator()
	    requests = (types.StreamingRecognizeRequest(audio_content=content)
	                for content in audio_generator)

	    responses = client.streaming_recognize(streaming_config, requests)

	    # Now, put the transcription responses to use.

	    jawnson = beta.listen_print_loop(responses, service, DOCUMENT_ID, True)
	    DOCUMENT_ID = jawnson[1]

	    return render_template('command.html', text = jawnson[0])