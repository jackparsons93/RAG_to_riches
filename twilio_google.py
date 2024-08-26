from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse, Gather
import openai
import os
import json
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = "123456789"  # Use a persistent secret key in production

# Load OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

# Google Custom Search API Configuration
GOOGLE_SEARCH_ENGINE_ID = os.getenv('GOOGLE_CSE_ID') 

@app.route("/search_chiefs")
def search_chiefs():
    try:
        # Load token from token.json
        with open("token.json", "r") as token_file:
            token = json.load(token_file)
        access_token = token['access_token']

        # Query the Google Custom Search API
        query = "Kansas City Chiefs upcoming games"
        search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&cx={GOOGLE_SEARCH_ENGINE_ID}&access_token={access_token}"
        response = requests.get(search_url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Return the JSON response
        return response.json()
    except FileNotFoundError:
        return "Token file not found. Please ensure token.json is available.", 400
    except Exception as e:
        print(f"Error making API request: {str(e)}")  # Debugging output
        return f"An error occurred during the API request: {str(e)}", 400

@app.route("/voice", methods=['POST'])
def voice():
    response = VoiceResponse()

    # Greet the user and ask what they would like to know
    gather = Gather(input="speech", action="/handle_speech", method="POST")
    gather.say("Hello! You can ask me about upcoming Kansas City Chiefs games. What would you like to know?")
    response.append(gather)

    return str(response)

@app.route("/handle_speech", methods=['POST'])
def handle_speech():
    speech_result = request.form.get('SpeechResult', None)
    if speech_result:
        # Query the Google Custom Search API and get upcoming Chiefs games
        chiefs_info = search_chiefs()

        # Use OpenAI to extract and list the games, opponents, and times
        conversation_history = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": (
                "Here is a JSON response from a Google Custom Search API query:\n\n"
                f"{json.dumps(chiefs_info, indent=2)}\n\n"
                "Please extract and list the upcoming Kansas City Chiefs games, including the dates, opponents, and times."
            )}
        ]
        openai_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."}
            ] + conversation_history,
            max_tokens=150
        )

        parsed_data = openai_response.choices[0].message.content.strip()

        # Respond with the parsed data
        response = VoiceResponse()
        response.say(parsed_data)
        response.say("Is there anything else you would like to know?")
        gather = Gather(input="speech", action="/handle_speech", method="POST")
        response.append(gather)
        return str(response)
    
    # If no speech was recognized, prompt again
    response = VoiceResponse()
    response.say("Sorry, I didn't catch that. Could you please repeat?")
    gather = Gather(input="speech", action="/handle_speech", method="POST")
    response.append(gather)
    return str(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)