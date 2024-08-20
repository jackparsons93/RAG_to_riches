from flask import Flask, request, session
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv
import openai
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Endpoint to handle incoming voice calls
@app.route("/voice", methods=['POST'])
def voice():
    response = VoiceResponse()

    # Initialize conversation history in the session
    if 'conversation_history' not in session:
        session['conversation_history'] = []

    # Greet the user and ask them to say something
    response.say("Hello! I'm a chatbot powered by ChatGPT. What would you like to talk about today?")

    # Use Twilio's <Gather> to capture speech input from the user
    gather = Gather(input="speech", speechTimeout="auto", action="/transcribe", method="POST")
    response.append(gather)

    return str(response)

# Endpoint to handle the transcribed speech
@app.route("/transcribe", methods=['POST'])
def transcribe():
    # Get the transcription of the user's speech
    transcription_text = request.form['SpeechResult']
    print(f"User asked: {transcription_text}")

    # Check if the user said "goodbye"
    if "goodbye" in transcription_text.lower():
        response = VoiceResponse()
        response.say("Goodbye!")
        response.hangup()
        return str(response)

    # Append the user's input to the conversation history
    conversation_history = session.get('conversation_history', [])
    conversation_history.append({"role": "user", "content": transcription_text})
    
    # Get the response from ChatGPT using the updated API call
    chatgpt_response = chat_gpt_response_with_history(conversation_history)
    print(f"ChatGPT response: {chatgpt_response}")

    # Append ChatGPT's response to the conversation history
    conversation_history.append({"role": "assistant", "content": chatgpt_response})
    session['conversation_history'] = conversation_history  # Save updated conversation history

    # Respond to the user with the generated text from ChatGPT
    response = VoiceResponse()
    response.say(chatgpt_response)

    # Continue the conversation by using <Gather> again
    gather = Gather(input="speech", speechTimeout="auto", action="/transcribe", method="POST")
    response.append(gather)

    return str(response)

# Function to interact with OpenAI's ChatGPT with conversation history
def chat_gpt_response_with_history(conversation_history):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."}
        ] + conversation_history,
        max_tokens=150
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
