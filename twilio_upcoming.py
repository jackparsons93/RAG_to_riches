import os
import datetime
import speech_recognition as sr
from flask import Flask, request, session
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv
import openai
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define the scope with read/write access
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_google_calendar_service():
    """Authenticate and return the Google Calendar service."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def ask_openai_for_event_details(event_description):
    """Query the OpenAI API to extract event details."""
    gpt_prompt = (
        f"Extract the event details from the following description: '{event_description}'\n"
        "Please ensure the details are provided in the following format:\n"
        "Title: [Event Title]\n"
        "Date: [YYYY-MM-DD]\n"
        "Time: [HH:MM AM/PM]\n"
        "Location: [Event Location]\n"
    )
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": gpt_prompt}
        ],
        max_tokens=150
    )
    return response.choices[0].message.content.strip()

def extract_event_details(response):
    """Extract event details from GPT response."""
    event_details = {'summary': None, 'date': None, 'time': None, 'location': None}
    for line in response.splitlines():
        if "Title:" in line:
            event_details['summary'] = line.split("Title:")[1].strip()
        elif "Date:" in line:
            event_details['date'] = line.split("Date:")[1].strip()
        elif "Time:" in line:
            event_details['time'] = line.split("Time:")[1].strip()
        elif "Location:" in line:
            event_details['location'] = line.split("Location:")[1].strip()

    # Ensure the event is scheduled in the current year
    if event_details['date']:
        event_details['date'] = ensure_current_year(event_details['date'])

    return event_details

def ensure_current_year(date_str):
    """Ensure that the date is in the current year if no year is specified."""
    current_year = datetime.datetime.now().year
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        if date_obj.year < current_year:
            date_obj = date_obj.replace(year=current_year)
    except ValueError:
        # If the year is not provided, assume the current year
        date_obj = datetime.datetime.strptime(f"{current_year}-{date_str}", "%Y-%m-%d")
    return date_obj.strftime("%Y-%m-%d")

def format_datetime(date_str, time_str):
    """Format the date and time strings into ISO 8601."""
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    time_obj = datetime.datetime.strptime(time_str, "%I:%M %p")
    combined_datetime = datetime.datetime.combine(date_obj, time_obj.time())
    return combined_datetime.isoformat()

def add_event_to_calendar(service, summary, location, start_time, end_time, time_zone='America/Los_Angeles'):
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
    print(f"Event created: {event.get('htmlLink')}")

def get_upcoming_events(service, max_results=5):
    """Retrieve and return upcoming events from Google Calendar with natural language formatting."""
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=max_results, singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])
    
    if not events:
        return "No upcoming events found."

    event_list = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        start_datetime = datetime.datetime.fromisoformat(start)
        natural_date = start_datetime.strftime("%B %d, %Y")  # e.g., "August 20, 2024"
        natural_time = start_datetime.strftime("%I:%M %p")    # e.g., "10:00 AM"
        event_list.append(f"{event['summary']} on {natural_date} at {natural_time}")

    return "Here are your upcoming events: " + "; ".join(event_list)

def recognize_speech_from_audio(audio):
    """Convert audio to text using speech recognition."""
    recognizer = sr.Recognizer()
    try:
        text = recognizer.recognize_google(audio)
        print(f"Recognized speech: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None

# Endpoint to handle incoming voice calls
@app.route("/voice", methods=['POST'])
def voice():
    response = VoiceResponse()

    # Greet the user and ask if they want to add an event or hear upcoming events
    response.say("Hello! Would you like to add an event to your calendar, or hear your upcoming events?")

    # Use Twilio's <Gather> to capture speech input from the user
    gather = Gather(input="speech", speechTimeout="auto", action="/handle_action", method="POST")
    response.append(gather)

    return str(response)

# Endpoint to handle the user's response
@app.route("/handle_action", methods=['POST'])
def handle_action():
    # Get the transcription of the user's speech
    transcription_text = request.form['SpeechResult']
    print(f"User said: {transcription_text}")

    # Check if the user wants to hear upcoming events
    if "upcoming events" in transcription_text.lower():
        service = get_google_calendar_service()
        upcoming_events = get_upcoming_events(service)
        response = VoiceResponse()
        response.say(upcoming_events)
        return str(response)

    # If the user wants to add an event
    if "add an event" in transcription_text.lower() or "add event" in transcription_text.lower():
        response = VoiceResponse()
        response.say("What event would you like to add to your calendar?")
        gather = Gather(input="speech", speechTimeout="auto", action="/transcribe_event", method="POST")
        response.append(gather)
        return str(response)

    # Default response if the action is unclear
    response = VoiceResponse()
    response.say("Sorry, I didn't understand that. Please say 'add an event' or 'upcoming events'.")
    gather = Gather(input="speech", speechTimeout="auto", action="/handle_action", method="POST")
    response.append(gather)

    return str(response)

# Endpoint to handle the transcribed event description
@app.route("/transcribe_event", methods=['POST'])
def transcribe_event():
    # Get the transcription of the user's speech
    transcription_text = request.form['SpeechResult']
    print(f"Event description: {transcription_text}")

    # Use OpenAI to extract event details
    gpt_response = ask_openai_for_event_details(transcription_text)
    event_details = extract_event_details(gpt_response)

    # Format start and end times
    if 'date' in event_details and 'time' in event_details:
        start_time = format_datetime(event_details['date'], event_details['time'])
        end_time = (datetime.datetime.fromisoformat(start_time) + datetime.timedelta(hours=1)).isoformat()

        # Add event to Google Calendar
        service = get_google_calendar_service()
        add_event_to_calendar(
            service,
            summary=event_details['summary'],
            location=event_details['location'],
            start_time=start_time,
            end_time=end_time
        )
        response = VoiceResponse()
        response.say(f"Your event titled '{event_details['summary']}' has been added to your calendar.")
    else:
        response = VoiceResponse()
        response.say("Sorry, I couldn't extract the necessary details to add your event.")

    return str(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
