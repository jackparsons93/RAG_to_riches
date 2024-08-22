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

    # Automatically press the number 1
    '''response.play(digits="1")
    response.pause(length=12)
    response.play(digits="1")
    response.pause(length=1)
    response.play(digits="1")
    response.pause(length=1)
    response.play(digits="1")'''
    

    # Initialize conversation history and speed preference in the session
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    if 'speed_preference' not in session:
        session['speed_preference'] = 'fast'

    # Ask the user if they want a slow or fast response
    response.say("Hello Jesse, Would you like a slow response with pauses, or a fast response?")
    
    # Gather the user's preference for response speed
    gather = Gather(input="speech", speechTimeout="auto", action="/set_speed", method="POST")
    response.append(gather)

    return str(response)

# Endpoint to handle the user's speed preference
@app.route("/set_speed", methods=['POST'])
def set_speed():
    # Get the user's speed preference
    speed_preference = request.form['SpeechResult'].lower()
    print(f"User chose speed preference: {speed_preference}")

    # Set the speed preference in the session
    if "slow" in speed_preference:
        session['speed_preference'] = 'slow'
    else:
        session['speed_preference'] = 'fast'

    # Ask if the user wants to ask a general question or a multiple-choice question
    response = VoiceResponse()
    response.say("Thank you. Would you like to ask a general question or a multiple-choice question?")
    
    # Gather the user's choice
    gather = Gather(input="speech", speechTimeout="auto", action="/choose_question_type", method="POST")
    response.append(gather)

    return str(response)

# Endpoint to choose question type (general or multiple-choice)
@app.route("/choose_question_type", methods=['POST'])
def choose_question_type():
    question_type = request.form['SpeechResult'].lower()
    print(f"User chose question type: {question_type}")

    response = VoiceResponse()
    if "multiple choice" in question_type:
        response.say("Please state your question.")
        gather = Gather(input="speech", speechTimeout="auto", action="/get_question", method="POST")
    else:
        response.say("Please state your question.")
        gather = Gather(input="speech", speechTimeout="auto", action="/transcribe", method="POST")
    
    response.append(gather)
    return str(response)

# Endpoint to handle the question entry
@app.route("/get_question", methods=['POST'])
def get_question():
    session['mcq_question'] = request.form['SpeechResult']
    print(f"User's question: {session['mcq_question']}")

    response = VoiceResponse()
    response.say("Thank you. Please state option A.")
    
    gather = Gather(input="speech", speechTimeout="auto", action="/get_option_a", method="POST")
    response.append(gather)
    return str(response)

# Endpoint to handle option A entry
@app.route("/get_option_a", methods=['POST'])
def get_option_a():
    session['mcq_option_a'] = request.form['SpeechResult']
    print(f"Option A: {session['mcq_option_a']}")

    response = VoiceResponse()
    response.say("Thank you. Please state option B.")
    
    gather = Gather(input="speech", speechTimeout="auto", action="/get_option_b", method="POST")
    response.append(gather)
    return str(response)

# Endpoint to handle option B entry
@app.route("/get_option_b", methods=['POST'])
def get_option_b():
    session['mcq_option_b'] = request.form['SpeechResult']
    print(f"Option B: {session['mcq_option_b']}")

    response = VoiceResponse()
    response.say("Thank you. Please state option C.")
    
    gather = Gather(input="speech", speechTimeout="auto", action="/get_option_c", method="POST")
    response.append(gather)
    return str(response)

# Endpoint to handle option C entry
@app.route("/get_option_c", methods=['POST'])
def get_option_c():
    session['mcq_option_c'] = request.form['SpeechResult']
    print(f"Option C: {session['mcq_option_c']}")

    response = VoiceResponse()
    response.say("Thank you. Please state option D.")
    
    gather = Gather(input="speech", speechTimeout="auto", action="/get_option_d", method="POST")
    response.append(gather)
    return str(response)

@app.route("/get_option_d", methods=['POST'])
def get_option_d():
    session['mcq_option_d'] = request.form['SpeechResult']
    print(f"Option D: {session['mcq_option_d']}")

    # Combine the question and options into a single string
    mcq_full_question = f"Question: {session['mcq_question']}\nA. {session['mcq_option_a']}\nB. {session['mcq_option_b']}\nC. {session['mcq_option_c']}\nD. {session['mcq_option_d']}"
    print(f"Full MCQ: {mcq_full_question}")

    # Send the multiple-choice question to ChatGPT
    chatgpt_response = chat_gpt_response_with_mcq(mcq_full_question)
    print(f"ChatGPT response: {chatgpt_response}")

    # Respond to the user with the ChatGPT answer
    response = VoiceResponse()
    response.say(chatgpt_response)

    # Automatically prompt the user for the next multiple-choice question
    response.say("Please state your next multiple-choice question.")
    
    # Gather the user's next multiple-choice question
    gather = Gather(input="speech", speechTimeout="auto", action="/get_question", method="POST")
    response.append(gather)

    return str(response)



# Function to interact with OpenAI's ChatGPT for multiple-choice questions
def chat_gpt_response_with_mcq(question_and_options):
    prompt = f"This is a multiple-choice question. Please choose the correct answer.\n\n{question_and_options}\n\nAnswer:"
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert at answering multiple-choice questions."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50
    )
    return response.choices[0].message.content.strip()

# Endpoint to handle the transcribed speech for general questions
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

    # Respond to the user based on their speed preference
    response = VoiceResponse()
    if session.get('speed_preference') == 'slow':
        speak_with_pauses(response, chatgpt_response)
    else:
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

# Function to split text into chunks of 4 words and add pauses in between
def speak_with_pauses(response, text):
    words = text.split()
    for i in range(0, len(words), 4):
        chunk = " ".join(words[i:i+4])
        response.say(chunk)
        if i + 4 < len(words):  # Add pause only if there are more words left
            response.pause(length=3)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
