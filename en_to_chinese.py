import speech_recognition as sr
from translate import Translator
from gtts import gTTS
from playsound import playsound
import os

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Please say something in English...")
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

def translate_text(text, dest_language='zh'):
    translator = Translator(to_lang=dest_language)
    translated = translator.translate(text)
    print(f"Translated Text: {translated}")
    return translated

def text_to_speech(text, language='zh'):
    tts = gTTS(text=text, lang=language)
    filename = "translated.mp3"
    tts.save(filename)
    playsound(filename)
    os.remove(filename)

def main():
    # Step 1: Capture English speech from the user
    english_text = recognize_speech()
    
    if english_text:
        # Step 2: Translate the captured speech to Chinese
        chinese_text = translate_text(english_text, dest_language='zh')

        # Step 3: Convert the translated text to speech in Chinese
        text_to_speech(chinese_text, language='zh')

if __name__ == "__main__":
    main()
