from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from twilio.twiml.voice_response import VoiceResponse, Gather
import os
import stripe
import random
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Set the database URI - the name of your SQLite database file
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Stripe
db = SQLAlchemy(app)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Create User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    passcode = db.Column(db.String(10), nullable=True)
    has_paid = db.Column(db.Boolean, default=False)

# Initialize the database
with app.app_context():
    db.create_all()

# Route for the login and registration page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'login' in request.form:
            # Handle the login
            username = request.form['username']
            password = request.form['password']

            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')

        elif 'register' in request.form:
            # Handle the registration
            username = request.form['username']
            password = request.form['password']

            # Check if the username already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists. Please choose another.', 'danger')
            else:
                # Create a new user and add to the database
                new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))

    return render_template('login.html')

# Route for the user dashboard (payment page)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(id=session['user_id']).first()

    if user.has_paid:
        return render_template('dashboard.html', passcode=user.passcode)
    else:
        return render_template('payment.html')

# Route to handle the payment process
@app.route('/pay', methods=['POST'])
def pay():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(id=session['user_id']).first()

    # Create a Stripe Checkout Session
    stripe_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'Premium Passcode',
                },
                'unit_amount': 500,  # $5.00
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=url_for('payment_success', _external=True),
        cancel_url=url_for('dashboard', _external=True),
    )

    return redirect(stripe_session.url)

# Route for successful payment
@app.route('/payment-success')
def payment_success():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(id=session['user_id']).first()

    # Generate a random 4-digit passcode
    user.passcode = str(random.randint(1000, 9999))
    user.has_paid = True
    db.session.commit()

    return redirect(url_for('dashboard'))

# Route for logging out
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Endpoint to handle incoming voice calls
@app.route("/voice", methods=['POST'])
def voice():
    response = VoiceResponse()

    # Initialize conversation history, speed preference, and attempt count in the session
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    if 'speed_preference' not in session:
        session['speed_preference'] = 'fast'
    if 'passcode_attempts' not in session:
        session['passcode_attempts'] = 0

    # Ask the user to enter a passcode
    response.say("Hello, please enter your passcode.")
    
    # Gather the passcode input from the user
    gather = Gather(input="dtmf", num_digits=4, action="/check_passcode", method="POST")
    response.append(gather)

    return str(response)

# Endpoint to check the passcode
@app.route("/check_passcode", methods=['POST'])
def check_passcode():
    passcode = request.form['Digits']
    print(f"User entered passcode: {passcode}")

    response = VoiceResponse()
    session['passcode_attempts'] += 1

    # Check if the passcode exists and is active in the database
    user = User.query.filter_by(passcode=passcode, has_paid=True).first()

    if user:
        # Reset the passcode attempt count
        session['passcode_attempts'] = 0
        
        response.say("Passcode accepted. Would you like a slow response with pauses, or a fast response?")
        
        # Gather the user's preference for response speed
        gather = Gather(input="speech", speechTimeout="auto", action="/set_speed", method="POST")
        response.append(gather)
    else:
        if session['passcode_attempts'] >= 2:
            response.say("Invalid passcode. Goodbye.")
            response.hangup()
        else:
            response.say("Invalid passcode. Please try again.")
            # Redirect to the voice endpoint to ask for the passcode again
            response.redirect("/voice")

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
