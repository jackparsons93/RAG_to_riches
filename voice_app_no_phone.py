import os
import tempfile
import openai
import speech_recognition as sr
from gtts import gTTS
from flask import Flask, session
import pygame

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize the speech recognizer
recognizer = sr.Recognizer()

# Initialize pygame mixer
pygame.mixer.init()

# Endpoint to start capturing audio from the microphone
@app.route("/capture", methods=['GET'])
def capture_audio():
    transcription_text = transcribe_from_microphone()
    
    if transcription_text:
        print(f"User said: {transcription_text}")
    else:
        return "Could not transcribe the audio.", 500
    
    # Check if the user said "goodbye"
    if "goodbye" in transcription_text.lower():
        response_text = "Goodbye!"
        play_text_to_speech(response_text)
        return response_text
    
    # Append the user's input to the conversation history
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    
    conversation_history = session.get('conversation_history', [])
    conversation_history.append({"role": "user", "content": transcription_text})
    
    # Get the response from ChatGPT using the updated API call
    chatgpt_response = chat_gpt_response_with_history(conversation_history)
    print(f"ChatGPT response: {chatgpt_response}")
    
    # Append ChatGPT's response to the conversation history
    conversation_history.append({"role": "assistant", "content": chatgpt_response})
    session['conversation_history'] = conversation_history  # Save updated conversation history

    # Convert the response to speech and play it
    play_text_to_speech(chatgpt_response)

    return chatgpt_response

# Function to capture and transcribe audio from the microphone
def transcribe_from_microphone():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            print("Listening...")
            audio_data = recognizer.listen(source)
            print("Processing...")
            transcription_text = recognizer.recognize_google(audio_data)
            return transcription_text
    except sr.UnknownValueError:
        print("Speech Recognition could not understand audio")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Speech Recognition service; {e}")
        return None

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

# Function to convert text to speech and play it using pygame
def play_text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    
    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)
    
    # Load the mp3 file using pygame and play it
    pygame.mixer.music.load(temp_file.name)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():  # Wait until the audio finishes playing
        continue

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
