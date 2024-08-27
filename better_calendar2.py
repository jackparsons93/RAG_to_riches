from flask import Flask, request, session, redirect, url_for
from twilio.twiml.voice_response import VoiceResponse, Gather
from datetime import datetime, timedelta
import openai
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import re

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define the scope with read/write access
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_google_calendar_service():
    """Authenticate and return the Google Calendar service."""
    creds = None
    token_path = 'token.json'
    
    # Check if the token file exists
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh token: {e}")
                # If refresh failed, delete the token file and reauthenticate
                if os.path.exists(token_path):
                    os.remove(token_path)
                return redirect(url_for('google_auth'))
        
        # If no valid credentials, initiate a new authorization flow
        if not creds:
            return redirect(url_for('google_auth'))
    
    return build('calendar', 'v3', credentials=creds)

@app.route('/google_auth')
def google_auth():
    """Initiate the OAuth flow to authenticate with Google and get a new token."""
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=8080)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    return redirect(url_for('voice'))

def ask_chatgpt_to_format_datetime(date_str, time_str):
    """Use ChatGPT to format the date and time for Google Calendar."""
    
    # One-shot learning example
    example_prompt = (
        "Example: \n"
        "Input: Date: September 15th, 2023, Time: 2 p.m.\n"
        "Output:\n"
        "Start Time: 2023-09-15T14:00:00-05:00\n"
        "End Time: 2023-09-15T15:00:00-05:00\n"
        "\n"
        f"Now convert the following date and time into the same format: \n"
        f"Date: {date_str}, Time: {time_str}."
    )
    
    gpt_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": example_prompt}
        ],
        max_tokens=150
    )
    
    # Extract the formatted times from GPT's response
    return gpt_response.choices[0].message.content.strip()


def add_event_to_calendar(service, summary, location, start_time, end_time, time_zone='America/Chicago'):
    """Add an event to Google Calendar."""
    event = {
        'summary': summary,
        'location': location,
        'start': {
            'dateTime': start_time,
            'timeZone': time_zone,
        },
        'end': {
            'dateTime': end_time,
            'timeZone': time_zone,
        },
        'reminders': {
            'useDefault': True,
        },
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('htmlLink')

@app.route("/voice", methods=['POST'])
def voice():
    response = VoiceResponse()
    response.say("Hello! Let's schedule a meeting.")
    
    gather = Gather(input="speech", speechTimeout="auto", action="/ask_time", method="POST")
    response.say("Who is the meeting with?")
    response.append(gather)
    
    return str(response)

@app.route("/ask_time", methods=['POST'])
def ask_time():
    transcription_text = request.form['SpeechResult']
    session['summary'] = f"Meeting with {transcription_text}"
    
    response = VoiceResponse()
    gather = Gather(input="speech", speechTimeout="auto", action="/ask_date", method="POST")
    response.say(f"At what time is the meeting with {transcription_text}?")
    response.append(gather)
    
    return str(response)

@app.route("/ask_date", methods=['POST'])
def ask_date():
    transcription_text = request.form['SpeechResult']
    session['time'] = transcription_text
    
    response = VoiceResponse()
    gather = Gather(input="speech", speechTimeout="auto", action="/confirm_event", method="POST")
    response.say(f"On what date is the meeting scheduled?")
    response.append(gather)
    
    return str(response)

@app.route("/confirm_event", methods=['POST'])
def confirm_event():
    transcription_text = request.form['SpeechResult']
    session['date'] = transcription_text

    # Use ChatGPT to format the date and time for Google Calendar
    gpt_response = ask_chatgpt_to_format_datetime(session['date'], session['time'])

    # Debugging: Print the GPT response to understand its format
    print(f"GPT Response: {gpt_response}")

    response = VoiceResponse()
    
    try:
        # Regular expression to extract start and end times
        start_time_match = re.search(r"Start Time:\s*(\S+)", gpt_response)
        end_time_match = re.search(r"End Time:\s*(\S+)", gpt_response)

        start_time_line = start_time_match.group(1) if start_time_match else None
        end_time_line = end_time_match.group(1) if end_time_match else None

        # Debugging: Print extracted times
        print(f"Start Time: {start_time_line}")
        print(f"End Time: {end_time_line}")

        if start_time_line and end_time_line:
            # Add the event to Google Calendar
            service = get_google_calendar_service()
            event_link = add_event_to_calendar(
                service,
                summary=session['summary'],
                location="",
                start_time=start_time_line,
                end_time=end_time_line,
                time_zone='America/Chicago'
            )
            response.say(f"Your meeting has been added to the calendar. You can view it here: {event_link}.")
        else:
            response.say("Sorry, there was an error processing the date and time. Please try again.")
    except Exception as e:
        # Print error for debugging
        print(f"Error: {e}")
        response.say("Sorry, there was an error adding the event to your calendar. Please try again.")
    
    return str(response)




if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
