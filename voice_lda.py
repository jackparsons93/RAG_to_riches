import speech_recognition as sr
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from gensim import corpora
from gensim.models import LdaModel
from gtts import gTTS
import os
from playsound import playsound

# Ensure necessary NLTK downloads
nltk.download('punkt')
nltk.download('stopwords')

# Function to speak text using gTTS
def speak(text):
    tts = gTTS(text=text, lang='en')
    tts.save("output.mp3")
    playsound("output.mp3")
    os.remove("output.mp3")

# Predefined dataset for LDA (Technology, Movies, Music topics)
data = {'text': [
    # Technology-related sentences
    "Artificial Intelligence is revolutionizing industries across the globe.",
    "Blockchain technology is transforming how we handle financial transactions.",
    "5G networks will bring faster internet speeds and lower latency for mobile users.",
    "Quantum computing could solve problems that are currently intractable.",
    "Tech companies are increasingly focused on developing clean energy solutions.",
    "Cybersecurity is becoming more important as more data moves to the cloud.",
    "Augmented reality and virtual reality are reshaping the gaming and entertainment sectors.",
    "Big data analytics allows businesses to make more informed decisions.",
    "Machine learning models require vast amounts of data for training.",
    "The future of autonomous vehicles looks promising with rapid advancements in AI.",
    "Smart homes use IoT devices to provide convenience and automation for users.",
    "Renewable energy technologies are critical to addressing climate change.",
    "Cloud computing platforms have become essential for modern business operations.",
    "Wearable technology, such as smartwatches, is enhancing personal health monitoring.",
    "Edge computing is reducing latency by processing data closer to where it is generated.",
    
    # Movies-related sentences
    "The Marvel Cinematic Universe has become one of the most successful film franchises in history.",
    "Film directors often use symbolism and imagery to convey deeper meanings in their work.",
    "Horror movies often play on people's psychological fears.",
    "Documentary films provide an in-depth look at real-world issues and events.",
    "Animated movies are not just for children, they are enjoyed by audiences of all ages.",
    "Special effects in modern films are incredibly advanced, making scenes more realistic.",
    "Many movies are adaptations of bestselling novels.",
    "The film industry has been significantly impacted by the rise of streaming services.",
    "The Oscars are one of the most prestigious awards ceremonies in the film industry.",
    "Science fiction movies often explore themes related to futuristic technologies and space exploration.",
    "Romantic comedies typically focus on the humorous side of love and relationships.",
    "Independent films often challenge traditional storytelling conventions.",
    "Cinematography plays a crucial role in how the audience perceives a movie.",
    "Action movies are known for their intense fight scenes and stunts.",
    "Classic films are still beloved by modern audiences and have stood the test of time.",
    "Many movies explore complex themes such as identity, morality, and justice.",
    "Actors undergo intensive training to prepare for roles that require physical transformations.",
    "Film festivals showcase a wide variety of genres, from indie films to big-budget blockbusters.",
    "Period dramas focus on a specific time in history, bringing the past to life through costumes and settings.",
    "Musical films combine singing, dancing, and acting into one cohesive narrative.",
    
    # Music-related sentences
    "Jazz music has a rich history and has influenced many other genres.",
    "Pop music is known for its catchy hooks and widespread appeal.",
    "Classical composers like Beethoven and Mozart have left a lasting legacy on music.",
    "The rise of streaming services has completely transformed the music industry.",
    "Hip hop has become one of the most popular genres in modern music.",
    "Live music performances offer a unique experience that recorded music cannot match.",
    "Musicians often draw inspiration from their personal experiences when writing songs.",
    "Electronic music is characterized by its use of synthesizers and drum machines.",
    "Country music often tells stories about love, loss, and life in rural America.",
    "Rock music evolved in the 1950s and has since diversified into many subgenres.",
    "Musical instruments like the guitar and piano are staples in many genres.",
    "Music festivals bring together artists from various genres for live performances.",
    "The music industry relies heavily on tours and concerts for revenue.",
    "Music theory helps musicians understand the structure and composition of songs.",
    "Many modern pop songs feature collaborations between multiple artists.",
    "The role of a music producer is to oversee the recording process and help shape the sound.",
    "Streaming platforms have given independent artists more opportunities to reach audiences.",
    "Music videos are often used to visually represent a song's themes and message.",
    "Folk music reflects the traditions and cultures of different regions around the world.",
    "Heavy metal music is known for its loud, aggressive sound and powerful lyrics.",
    "Reggae music originated in Jamaica and is recognized for its relaxed rhythms and socially conscious lyrics.",
    "Music education plays an important role in developing young musicians' talents.",
    "K-Pop has gained international popularity due to its energetic performances and devoted fan base.",
    "Jazz improvisation allows musicians to explore creative ways of expressing melodies and harmonies.",
    "Opera combines music, drama, and visual art into one immersive experience."
]}


# Preprocess function: Clean text, tokenize, remove stopwords
def preprocess(text):
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    text = re.sub(r'\W', ' ', text)   # Remove non-alphabetic characters
    text = text.lower()               # Convert to lowercase
    tokens = word_tokenize(text)      # Tokenize
    stop_words = set(stopwords.words('english'))  # Remove stopwords
    tokens = [word for word in tokens if word not in stop_words]
    return tokens

# LDA preparation
processed_texts = [preprocess(text) for text in data['text']]
dictionary = corpora.Dictionary(processed_texts)
corpus = [dictionary.doc2bow(text) for text in processed_texts]

# Train the LDA model on predefined text corpus
lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=3, passes=10, random_state=100)

# Function to predict the topic from the user's input
def predict_topic(text):
    processed_text = preprocess(text)
    bow_vector = dictionary.doc2bow(processed_text)
    topic_distribution = lda_model.get_document_topics(bow_vector)
    topic, probability = max(topic_distribution, key=lambda item: item[1])  # Get the topic with the highest probability
    return topic, probability

# Speech recognition and topic prediction
def listen_and_predict():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        # Say the initial prompt
        speak("What would you like to talk about today?")
        print("Please say something...")

        audio = recognizer.listen(source)

    try:
        # Convert speech to text using Google's speech recognition
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")

        # Predict the topic of the spoken input
        topic, probability = predict_topic(text)

        # Output the detected topic
        if topic == 0:
            response = f"The topic is Technology with a probability of {probability:.2f}"
        elif topic == 1:
            response = f"The topic is Movies with a probability of {probability:.2f}"
        else:
            response = f"The topic is Music with a probability of {probability:.2f}"

        # Speak the result out loud
        speak(response)

    except sr.UnknownValueError:
        speak("Sorry, I couldn't understand your speech.")
    except sr.RequestError as e:
        speak(f"Could not request results from the speech recognition service; {e}")

# Run the voice input and prediction
if __name__ == "__main__":
    listen_and_predict()
