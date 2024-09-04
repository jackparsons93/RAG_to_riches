# RAG_to_riches
The code in the folder flask_stripe is a flask app that has the user input a test credit card (all 42's) into stripe and then it gives the user a passcode that can then be input over the phone using twilio, if the passcode is incorrect, it will deny them access, but if the passcode is correct it will allow them to ask questions to ChatGPT.

Better_calendar2.py is a twilio program that allows the user to create google calendar events using twilio.

chat_gpt_summarizer.py takes in speech using python's speech_recognition library and then asks a question to ChatGPT and then summarizes the data using transformers

en_to_chinese.py Takes english as the input and outputs Chinese again, using speech_recognition, translate, and gtts libraries

lda_topics.py uses NLP and machine learning to do Latent Dirichlet Allocation and outputs an html file using pyLDAvis

light_flash.py uses sound recognition and a raspberry pi to flash a light on voice command

memory.py is a program that uses twilio and session['conversation_history'] to save ChatGPT memories so ChatGPT can repeat itself.

multiple.py is a program that uses twilio and chatGPT to ask the user for a general question or a multiple choice question, and if multiple choice it will ask options A-D, then ask the next question.

passcode.py is a precursor to flask_stripe, where the user must enter the passcode 1337 to get to ask a question to ChatGPT

pdf.py is a program that takes a pdf input and splits it into questions then asks each question to ChatGPT and then returns a completed pdf

speech_calendar.py Uses the google calendar API, ChatGPT, sound recognition library,  and one-shot prompting to create an event on google calendar or check events coming up.

twilio_calendar.py Is like speech calendar and allows you to create events using Twilio and the google calendar API

twilio_google.py Is a Twilio and google search API tool that uses ChatGPT to parse upcoming chiefs games from the google search API.

twilio_persistant.py is one of the original programs that does not hangup automatically after you ask a question and allows you ask multiple questions.

twilio_vader.py uses nltk vader sentiment analysis to check to see if the user is unhappy, and then if they are unhappy it will forward the call to a human representative

twilly.py is the original ChatGPT and Twilio program that just simpl asks a question to ChatGPT and then hangs up after speaking the answer to the question

user_db.py is a natural language database application that could in the future be used with voice, that allows the user to use natural language to interact with a basic CRUD Web APP including accessing a database.

vader_sentiment.py is a vader nltk program that will detect if the user is happy or sad and reroute the voice chat based on what the user is feeling.

voice_app_no_phone.py Is a sound recognition, google text-to-speech gtts and ChatGPT app, that uses memory to remember what ChatGPT has said before.

voice_lda.py Is a latent dirichlet allocation app that summarizes topics based on user speech input

wikipedia_summarizer.py is a beautiful soup wikipedia web scraper that summarizes the text using transformers.

