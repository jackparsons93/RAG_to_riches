import os
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Download the VADER lexicon for sentiment analysis
nltk.download('vader_lexicon')

app = Flask(__name__)

# Twilio credentials from environment variables
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# OpenAI API Key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

# The number to forward the call to if sentiment is negative
forward_number = "+18162560783"

# Initialize the sentiment analyzer
sid = SentimentIntensityAnalyzer()

@app.route("/voice", methods=['POST'])
def voice():
    response = VoiceResponse()

    # Prompt the user to speak their thoughts
    gather = Gather(input="speech", action="/process_speech", method="POST")
    gather.say("Please tell me how you are feeling today.")
    response.append(gather)

    return str(response)

@app.route("/process_speech", methods=['POST'])
def process_speech():
    response = VoiceResponse()

    # Get the user's speech input
    user_input = request.form['SpeechResult']

    # Analyze the sentiment
    sentiment_scores = sid.polarity_scores(user_input)
    compound_score = sentiment_scores['compound']

    if compound_score < 0:
        # Forward the call if sentiment is negative
        response.say("I'm sorry to hear that you're having a tough time. Let me connect you to someone who can help.")
        response.dial(forward_number)
        response.hangup()  # Ensure the call ends after dialing
    else:
        # If sentiment is positive, ask the user to ask a question
        gather = Gather(input="speech", action="/chatgpt", method="POST")
        gather.say("I'm glad to hear that you're doing well. You can now ask me any question.")
        response.append(gather)

    return str(response)

@app.route("/chatgpt", methods=['POST'])
def chatgpt():
    response = VoiceResponse()

    # Get the user's question
    user_question = request.form['SpeechResult']

    # Send the question to OpenAI's ChatGPT
    chat_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert at answering multiple-choice questions."},
            {"role": "user", "content": user_question}
        ],
        max_tokens=50
    )
    
    answer = chat_response.choices[0].message.content.strip()

    # Respond with the answer from ChatGPT spoken out loud
    response.say(f"Here is the answer to your question: {answer}")

    return str(response)

if __name__ == "__main__":
    app.run(port=8080, debug=True)
