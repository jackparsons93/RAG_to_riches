import os
import datetime
import speech_recognition as sr
from dotenv import load_dotenv
from openai import OpenAI
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Load environment variables from .env file
load_dotenv()

# Get the OpenAI API key from the environment
openai_api_key = os.getenv('OPENAI_API_KEY')

# Set up OpenAI API client
client = OpenAI(api_key=openai_api_key)

# Define the scope with read/write access
SCOPES = ['https://www.googleapis.com/auth/calendar']

def ask_openai_for_event_details(event_description):
    """Query the OpenAI API with a natural language question to extract event details."""
    gpt_prompt = (
        f"Extract the event details from the following description: '{event_description}'\n"
        "Please ensure the details are provided in the following format:\n"
        "Title: [Event Title]\n"
        "Date: [YYYY-MM-DD]\n"
        "Time: [HH:MM AM/PM]\n"
        "Location: [Event Location]\n\n"
        "Example:\n"
        "'Meeting with John on March 15th at 3:00 PM at 123 Main St.' should be parsed as:\n"
        "Title: Meeting with John\n"
        "Date: 2024-03-15\n"
        "Time: 03:00 PM\n"
        "Location: 123 Main St.\n\n"
        "Please parse the provided event description accordingly."
    )
    response = client.chat.completions.create(
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
    print("GPT Response:\n", response)  # Debugging: print the raw GPT response
    
    # Initialize the dictionary to hold event details
    event_details = {'summary': None, 'date': None, 'time': None, 'location': None}

    # Process the response line by line
    for line in response.splitlines():
        if "Title:" in line:
            event_details['summary'] = line.split("Title:")[1].strip()
        elif "Date:" in line:
            event_details['date'] = line.split("Date:")[1].strip()
        elif "Time:" in line:
            event_details['time'] = line.split("Time:")[1].strip()
        elif "Location:" in line:
            event_details['location'] = line.split("Location:")[1].strip()

    # Debugging: Print the extracted details
    print("Extracted Event Details:", event_details)
    
    # Ensure all necessary details were extracted
    if None in event_details.values():
        print("Error: Some details could not be extracted properly.")
    
    return event_details

def format_datetime(date_str, time_str):
    """Format the date and time strings into ISO 8601."""
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    time_obj = datetime.datetime.strptime(time_str, "%I:%M %p")  # Handle AM/PM
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

def get_upcoming_events(service, max_results=10):
    """Retrieve upcoming events from Google Calendar."""
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=max_results, singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])
    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])

def recognize_speech():
    """Capture speech input and convert it to text."""
    recognizer = sr.Recognizer()

    # Print available microphone list
    print("Available microphones:")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"Microphone with index {index}: {name}")

    try:
        with sr.Microphone() as source:
            print("Microphone source:", source)
            print("Please say something...")
            audio = recognizer.listen(source)
            print("Recognizing speech...")
            try:
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
            except sr.UnknownValueError:
                print("Sorry, I could not understand the audio.")
                return None
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
                return None
    except Exception as e:
        print(f"An error occurred while accessing the microphone: {e}")
        return None


def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    while True:
        user_input = input("Enter 'add' to create a new event, 'check' to view upcoming events, 'speak' to use speech recognition, or 'exit' to quit: ").strip().lower()

        if user_input == 'add':
            event_description = input("Please describe the event you'd like to add: ")
            gpt_response = ask_openai_for_event_details(event_description)

            event_details = extract_event_details(gpt_response)

            if 'date' in event_details and 'time' in event_details:
                start_time = format_datetime(event_details['date'], event_details['time'])
                end_time = (datetime.datetime.fromisoformat(start_time) + datetime.timedelta(hours=1)).isoformat()

                add_event_to_calendar(
                    service,
                    summary=event_details['summary'],
                    location=event_details['location'],
                    start_time=start_time,
                    end_time=end_time
                )
            else:
                print("Error: Missing 'date' or 'time' in extracted event details.")

        elif user_input == 'check':
            get_upcoming_events(service)

        elif user_input == 'speak':
            speech_text = recognize_speech()
            if speech_text:
                gpt_response = ask_openai_for_event_details(speech_text)

                event_details = extract_event_details(gpt_response)

                if 'date' in event_details and 'time' in event_details:
                    start_time = format_datetime(event_details['date'], event_details['time'])
                    end_time = (datetime.datetime.fromisoformat(start_time) + datetime.timedelta(hours=1)).isoformat()

                    add_event_to_calendar(
                        service,
                        summary=event_details['summary'],
                        location=event_details['location'],
                        start_time=start_time,
                        end_time=end_time
                    )
                else:
                    print("Error: Missing 'date' or 'time' in extracted event details.")

        elif user_input == 'exit':
            print("Exiting program.")
            break

        else:
            print("Invalid input. Please enter 'add', 'check', 'speak', or 'exit'.")

if __name__ == '__main__':
    main()
