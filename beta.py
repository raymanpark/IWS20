from __future__ import division
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

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
SCOPES = ['https://www.googleapis.com/auth/documents']
DOCUMENT_ID = '' # The ID of a sample document.
str_request = ""
# from google.cloud import speech_v1
# from google.cloud.speech_v1 import enums

def createDocument(documentTitle, service):
    con = psycopg2.connect(host = "localhost", database = "easytext", user = "postgres", password = "abc123ef")
    cur = con.cursor()

    title = documentTitle
    body = {
        'title': title
    }
    doc = service.documents() \
        .create(body=body).execute()
    print('Created document with title: {0}'.format(
        doc.get('title')))

    piq = """ INSERT INTO documents (doc_id, doc_name) VALUES (%s,%s)"""
    ri = (doc['documentId'], title)
    cur.execute(piq, ri)
    con.commit()
    con.close()
    global DOCUMENT_ID 
    DOCUMENT_ID = doc['documentId']
    stringtoreturn = "Document, " + documentTitle + " Successfully Created!"
    return (stringtoreturn, DOCUMENT_ID)

def openDocument(documentTitle, service):
    global DOCUMENT_ID
    temp = DOCUMENT_ID
    con = psycopg2.connect(host = "localhost", database = "easytext", user = "postgres", password = "abc123ef")
    cur = con.cursor()
    psq = "SELECT * FROM documents"
    cur.execute(psq)
    table = cur.fetchall()
    for row in table:
        # print(row[0])
        # print(row[0].lower())
        if row[0].lower() == documentTitle:
            DOCUMENT_ID = row[1]
            print("Successfully opened")
            break
    con.commit()
    con.close()

    if DOCUMENT_ID == temp:
        return ("Unable to Find Document with that Title", DOCUMENT_ID)
    
    docBody_new = service.documents() \
        .get(documentId=documentID).execute()
    
    text = docBody_new['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    return (text, DOCUMENT_ID)

def deleteText(documentID, service, start, end):
    findex = 1
    lindex = 1

    docBody = service.documents() \
        .get(documentId=DOCUMENT_ID).execute()

    body = docBody['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']
    body = body.lower()

    if start not in body:
        stringtoreturn = start + " is not in the document"
        return (stringtoreturn, DOCUMENT_ID)
    if end not in body:
        stringtoreturn = end + " is not in the document"
        return (end, DOCUMENT_ID)

    findex = body.index(start) + 1
    lindex = body.index(end, findex) + len(end) + 1

    requests = [
        {
            'deleteContentRange': {
                'range': {
                    'startIndex': findex,
                    'endIndex': lindex,
                }

            }

        },
    ]

    service.documents().batchUpdate(
        documentId=documentID, body={'requests': requests}).execute()

    docBody_new = service.documents() \
        .get(documentId=documentID).execute()
    
    text = docBody_new['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    return (text, DOCUMENT_ID)

def deleteWord(documentID, service, word):
    docBody = service.documents() \
        .get(documentId=DOCUMENT_ID).execute()

    body = docBody['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']
    body = body.lower()

    if word not in body:
        stringtoreturn = word + " not in the document"
        return (stringtoreturn, DOCUMENT_ID)

    findex = body.index(word)
    wordlen = len(word)
    lindex = findex + wordlen + 1

    requests = [
        {
            'deleteContentRange': {
                'range': {
                    'startIndex': findex,
                    'endIndex': lindex,
                }

            }

        },
    ]

    service.documents().batchUpdate(
        documentId=documentID, body={'requests': requests}).execute()
    docBody_new = service.documents() \
        .get(documentId=documentID).execute()
    
    text = docBody_new['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    return (text, DOCUMENT_ID)

def writeText(documentID, service, request):
    docBody = service.documents() \
        .get(documentId=documentID).execute()
    
    docBody = docBody['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    index = len(docBody)

    edits = [
        {
            'insertText': {
                'location': {
                    'index': index,
                },
                'text': request
            }
        }
    ]

    service.documents().batchUpdate(documentId=documentID, body={'requests': edits}).execute()

    docBody_new = service.documents() \
        .get(documentId=documentID).execute()
    
    text = docBody_new['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    return (text, DOCUMENT_ID)


def insertText(documentID, service, request, substring):
    request = " " + request

    docBody = service.documents() \
        .get(documentId=documentID).execute()
    
    docBody = docBody['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    if substring not in docBody:
        stringtoreturn = substring + " not in the document"
        return (stringtoreturn, DOCUMENT_ID)

    index = docBody.index(substring) + len(substring) + 1

    edits = [
        {
            'insertText': {
                'location': {
                    'index': index,
                },
                'text': request
            }
        }
    ]

    service.documents().batchUpdate(documentId=documentID, body={'requests': edits}).execute()

    docBody_new = service.documents() \
        .get(documentId=documentID).execute()
    
    text = docBody_new['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    return (text, DOCUMENT_ID)

def copy(documentID, service, start, end):
    docBody = service.documents() \
        .get(documentId=documentID).execute()
    
    docBody = docBody['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    if start not in docBody:
        stringtoreturn = start + " not in your document"
        return (stringtoreturn, DOCUMENT_ID)
    if end not in docBody:
        stringtoreturn = end + " not in your document"
        return (stringtoreturn, DOCUMENT_ID)

    findex = docBody.index(start)
    lindex = docBody.index(end) + len(end)

    target = docBody[findex:lindex]
    pyperclip.copy(target)

    return ("Successfully Copied!", DOCUMENT_ID)

def pasteAt(documentID, service, at):
    docBody = service.documents() \
        .get(documentId=documentID).execute()
    
    docBody = docBody['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    if at not in docBody:
        stringtoreturn = at + " not in the document"
        return (stringtoreturn, DOCUMENT_ID)

    index = docBody.index(at) + len(at) + 1

    request = " " + pyperclip.paste()

    edits = [
        {
            'insertText': {
                'location': {
                    'index': index,
                },
                'text': request
            }
        }
    ]

    service.documents().batchUpdate(documentId=documentID, body={'requests': edits}).execute()
    
    docBody_new = service.documents() \
        .get(documentId=documentID).execute()
    
    text = docBody_new['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    return (text, DOCUMENT_ID)

def comma_at(documentID, service, at):
    docBody = service.documents() \
        .get(documentId=documentID).execute()
    
    docBody = docBody['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    if at not in docBody:
        stringtoreturn = at + " not in the document"
        return (stringtoreturn, DOCUMENT_ID)

    index = docBody.index(at) + len(at) + 1

    request = ", "

    edits = [
        {
            'insertText': {
                'location': {
                    'index': index,
                },
                'text': request
            }
        }
    ]

    service.documents().batchUpdate(documentId=documentID, body={'requests': edits}).execute()
    
    docBody_new = service.documents() \
        .get(documentId=documentID).execute()
    
    text = docBody_new['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    return (text, DOCUMENT_ID)

def period_at(documentID, service, at):
    docBody = service.documents() \
        .get(documentId=documentID).execute()
    
    docBody = docBody['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    if at not in docBody:
        stringtoreturn = at + " not in the document"
        return (stringtoreturn, DOCUMENT_ID)

    index = docBody.index(at) + len(at) + 1

    request = ". "

    edits = [
        {
            'insertText': {
                'location': {
                    'index': index,
                },
                'text': request
            }
        }
    ]

    service.documents().batchUpdate(documentId=documentID, body={'requests': edits}).execute()
    
    docBody_new = service.documents() \
        .get(documentId=documentID).execute()
    
    text = docBody_new['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    return (text, DOCUMENT_ID)

def comma(DocumentID, service):
    docBody = service.documents() \
        .get(documentId=documentID).execute()
    
    docBody = docBody['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    index = len(docBody)

    request = ", "

    edits = [
        {
            'insertText': {
                'location': {
                    'index': index,
                },
                'text': request
            }
        }
    ]

    service.documents().batchUpdate(documentId=documentID, body={'requests': edits}).execute()

    docBody_new = service.documents() \
        .get(documentId=documentID).execute()
    
    text = docBody_new['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    return (text, DOCUMENT_ID)

def comma(DocumentID, service):
    docBody = service.documents() \
        .get(documentId=documentID).execute()
    
    docBody = docBody['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    index = len(docBody)

    request = ". "

    edits = [
        {
            'insertText': {
                'location': {
                    'index': index,
                },
                'text': request
            }
        }
    ]

    service.documents().batchUpdate(documentId=documentID, body={'requests': edits}).execute()

    docBody_new = service.documents() \
        .get(documentId=documentID).execute()
    
    text = docBody_new['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    return (text, DOCUMENT_ID)

def replace(documentID, service, original, replacement):
    docBody = service.documents() \
        .get(documentId=documentID).execute()
    
    docBody = docBody['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    if original not in docBody:
        stringtoreturn = original + " not in the document"
        return (stringtoreturn, DOCUMENT_ID)

    index = docBody.index(original)
    deleteWord(documentID, service, original)
    replacement = ' ' + replacement

    edits = [
        {
            'insertText': {
                'location': {
                    'index': index,
                },
                'text': replacement
            }
        }
    ]

    service.documents().batchUpdate(documentId=documentID, body={'requests': edits}).execute()
    
    docBody_new = service.documents() \
        .get(documentId=documentID).execute()
    
    text = docBody_new['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    return (text, DOCUMENT_ID)

def replaceAll(documentID, service, original, replacement):
    docBody = service.documents() \
        .get(documentId=documentID).execute()
    
    docBody = docBody['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    while original in docBody:
        replace(documentID, service, original, replacement)
        
        docBody = service.documents() \
            .get(documentId=documentID).execute()
        docBody = docBody['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    docBody_new = service.documents() \
        .get(documentId=documentID).execute()
    
    text = docBody_new['body']['content'][1]['paragraph']['elements'][0]['textRun']['content']

    return (text, DOCUMENT_ID)

class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1, rate=self._rate,
            input=True, frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)


def listen_print_loop(responses, service, documentID, cmd):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """

    global DOCUMENT_ID
    num_chars_printed = 0
    if documentID == "":
        con = psycopg2.connect(host = "localhost", database = "easytext", user = "postgres", password = "abc123ef")
        cur = con.cursor()
        psq = "SELECT * FROM documents"
        cur.execute(psq)
        row = cur.fetchone()
        documentID = row[1]
        con.commit()
        con.close()

    DOCUMENT_ID = documentID

    print("Document ID is ", documentID)
    for response in responses:
        # if keyboard.is_pressed(' '):
        #     print("Space Pressed")

        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            print(transcript + overwrite_chars)

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            # if re.search(r'\b(exit|quit)\b', transcript, re.I):
            #     print('Exiting..')
            #     break

            num_chars_printed = 0

            # changed
            if cmd == True:
                client_request = transcript + overwrite_chars
            #     #service = build('docs', 'v1', credentials=None)

                if "create" in client_request:
                    title = client_request.split("create", 1)[1]
                    title = title.strip()
                    title = title[0].upper() + title[1:]
                    return createDocument(title, service)
                elif "open" in client_request:
                    title = client_request.split("open", 1)[1]
                    title = title.strip()
                    return openDocument(title, service)
                elif "delete" in client_request:
                    if "from" in client_request and "to" in client_request:
                        # findex = body.index(start)
                        # lindex = body.index(end, findex)
                        start = re.search('from(.*)to', client_request).group(1).strip().lower()
                        findex = client_request.index(start)
                        i_to = client_request.index('to', findex)
                        end = client_request[i_to + 2:].strip().lower()
                        print(start, end)
                        return deleteText(DOCUMENT_ID, service, start, end)
                    else:
                        word = client_request.split("delete", 1)[1]
                        word = word.strip()
                        return deleteWord(DOCUMENT_ID, service, word)
                elif "insert" in client_request:
                    if "after" in client_request:
                        request = re.search('insert(.*)after', client_request).group(1).strip()
                        findex = client_request.index(request)
                        index = client_request.index('after', findex)
                        substring = client_request[index + 5:].strip()
                        return insertText(DOCUMENT_ID, service, request, substring)
                elif "copy" in client_request:
                    if "from" in client_request and "to" in client_request:
                        # findex = body.index(start)
                        # lindex = body.index(end, findex)
                        start = re.search('from(.*)to', client_request).group(1).strip()
                        findex = client_request.index(start)
                        i_to = client_request.index('to', findex)
                        end = client_request[i_to + 2:].strip()
                        return copy(DOCUMENT_ID, service, start, end)
                elif "paste" in client_request:
                    if "after" in client_request:
                        at = client_request.split("after", 1)[1]
                        at = at.strip()
                        return pasteAt(DOCUMENT_ID, service, at)
                elif "replace all" in client_request:
                    if "with" in client_request:
                        original = re.search('all(.*)with', client_request).group(1).strip()
                        findex = client_request.index(original)
                        i_with = client_request.index('with', findex)
                        replacement = client_request[i_with + 4:].strip()
                        return replaceAll(DOCUMENT_ID, service, original, replacement)

                elif "replace" in client_request:
                    if "with" in client_request:
                        original = re.search('replace(.*)with', client_request).group(1).strip()
                        findex = client_request.index(original)
                        i_with = client_request.index('with', findex)
                        replacement = client_request[i_with + 4:].strip()
                        return replace(DOCUMENT_ID, service, original, replacement)

                elif "," in client_request:
                    if "after" in client_request:
                        at = client_request.split("after", 1)[1]
                        at = at.strip()
                        return comma_at(DOCUMENT_ID, service, at)
                    else:
                        return comma(DOCUMENT_ID, service)

                elif "." in client_request:
                    if "after" in client_request:
                        at = client_request.client_request.split("after", 1)[1]
                        at = at.strip()
                        return period_at(DOCUMENT_ID, service, at)
                    else:
                        return period(DOCUMENT_ID, service)
                else:
                    return ("That was not a recognized command", DOCUMENT_ID)

            #     potential_command = False
            #     command = False


            # elif potential_command == True:
            #     if "yes" in transcript + overwrite_chars:
            #         command = True
            #         print("What is your request?")
            #     else:
            #         potential_command = False
            #         str_request = remainder.strip()
            #         str_request = str_request[0].upper() + str_request[1:] + ". "
            #         writeText(DOCUMENT_ID, service, str_request)

            # elif trigger in (transcript + overwrite_chars):
            #     potential_command = True
            #     myString = transcript + overwrite_chars
            #     remainder = myString.split(trigger, 1)[1]
            #     print("Do you want to use a command (Yes or No)?")

            # elif DOCUMENT_ID == "":
            #     print("You have not chosen a document")

            else:
                str_request = transcript + overwrite_chars
                str_request = str_request.strip()
                str_request = str_request[0].upper() + str_request[1:] + ". "
                return writeText(DOCUMENT_ID, service, str_request)

def main():
    """Shows basic usage of the Docs API.
    Prints the title of a sample document.
    """
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

    print("Please open existing or create new document")

    language_code = 'en-US'  # a BCP-47 language tag

    client = speech.SpeechClient()
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code)
    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=False)

    openDocument("Hello World", service)

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (types.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        listen_print_loop(responses, service, DOCUMENT_ID)

if __name__ == '__main__':
    main()