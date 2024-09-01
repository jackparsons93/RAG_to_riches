import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import os
import openai
from transformers import pipeline
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Download the VADER lexicon for sentiment analysis
nltk.download('vader_lexicon')

# Initialize the sentiment analyzer
sid = SentimentIntensityAnalyzer()

# Initialize the summarization pipeline
summarizer = pipeline("summarization")

# OpenAI API Key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')

def recognize_speech_from_streaming_audio(prompt=""):
    recognizer = sr.Recognizer()

    # Adjust to use the "Audio Streaming" source
    with sr.Microphone(device_index=3) as source:  # Adjust device_index as needed
        if prompt:
            text_to_speech(prompt)
        print("Listening to the audio stream...")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand what you said.")
        return None
    except sr.RequestError:
        print("Sorry, the service is not available.")
        return None

def analyze_sentiment(text):
    sentiment_scores = sid.polarity_scores(text)
    return sentiment_scores

def text_to_speech(text):
    tts = gTTS(text=text, lang='en')
    filename = "response.mp3"
    tts.save(filename)
    playsound(filename)
    os.remove(filename)

def get_chatgpt_response(user_question):
    chat_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert at answering questions."},
            {"role": "user", "content": user_question}
        ],
        max_tokens=150
    )
    answer = chat_response.choices[0].message.content.strip()
    
    return answer

def summarize_text(text):
    # Set max_length and min_length to aim for around 30 words
    max_length = 45  # Approx. 30 words
    min_length = 45  # Approx. 30 words
    
    summarized_answer = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)[0]['summary_text']
    return summarized_answer

def main():
    # Start by asking the user how they are doing
    initial_prompt = "Hello! How are you doing today?"
    text_to_speech(initial_prompt)

    # Step 1: Get the user's response about how they are doing
    user_input = recognize_speech_from_streaming_audio()

    if user_input:
        # Step 2: Perform sentiment analysis
        sentiment_scores = analyze_sentiment(user_input)
        compound_score = sentiment_scores['compound']

        # Step 3: Generate response based on sentiment
        if compound_score >= 0.05:
            response = "I am glad you are happy. What question would you like to ask?"
            print(f"Response: {response}")
            text_to_speech(response)

            # Step 4: Get the user's question for ChatGPT
            user_question = recognize_speech_from_streaming_audio("Please ask your question.")

            if user_question:
                # Step 5: Get the response from ChatGPT
                chatgpt_response = get_chatgpt_response(user_question)
                print(f"ChatGPT Response: {chatgpt_response}")
                
                # Step 6: Summarize the response to 30 words
                summarized_response = summarize_text(chatgpt_response)
                print(f"Summarized Response: {summarized_response}")
                
                # Step 7: Convert the summarized response to speech and play it
                text_to_speech(f"Here is the summarized response: {summarized_response}")
        elif compound_score <= -0.05:
            response = "I am sorry you are having a bad day."
            print(f"Response: {response}")
            text_to_speech(response)
        else:
            response = "I hope you are doing well."
            print(f"Response: {response}")
            text_to_speech(response)

if __name__ == "__main__":
    main()
