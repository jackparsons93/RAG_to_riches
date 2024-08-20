from flask import Flask, request, make_response
from twilio.twiml.voice_response import VoiceResponse, Gather
import openai

# Initialize Flask app
app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = ''

# Endpoint to handle incoming voice calls
@app.route("/voice", methods=['POST'])
def voice():
    response = VoiceResponse()

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

    # Get the response from ChatGPT
    chatgpt_response = chat_gpt_response(transcription_text)
    print(f"ChatGPT response: {chatgpt_response}")

    # Respond to the user with the generated text from ChatGPT
    response = VoiceResponse()
    response.say(chatgpt_response)

    # Optionally, allow the user to continue the conversation
    gather = Gather(input="speech", speechTimeout="auto", action="/transcribe", method="POST")
    response.append(gather)

    return str(response)

# Function to interact with OpenAI's ChatGPT
def chat_gpt_response(prompt):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150
    )
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
