import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import os

# Download the VADER lexicon for sentiment analysis
nltk.download('vader_lexicon')

# Initialize the sentiment analyzer
sid = SentimentIntensityAnalyzer()

def recognize_speech_from_streaming_audio():
    recognizer = sr.Recognizer()

    # Adjust to use the "Audio Streaming" source
    with sr.Microphone(device_index=3) as source:  # You may need to adjust the device_index
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

def main():
    # Step 1: Get speech input from the user via audio streaming
    user_input = recognize_speech_from_streaming_audio()

    if user_input:
        # Step 2: Perform sentiment analysis
        sentiment_scores = analyze_sentiment(user_input)
        compound_score = sentiment_scores['compound']

        # Step 3: Generate response based on sentiment
        if compound_score >= 0.05:
            response = "I am glad you are happy."
        elif compound_score <= -0.05:
            response = "I am sorry you are having a bad day."
        else:
            response = "I hope you are doing well."

        print(f"Response: {response}")

        # Step 4: Convert the response to speech and play it
        text_to_speech(response)

if __name__ == "__main__":
    main()
