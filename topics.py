import speech_recognition as sr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from gtts import gTTS
import os
from playsound import playsound

# Function to speak text using Google TTS
def speak(text):
    tts = gTTS(text=text, lang='en')
    filename = "speech.mp3"
    tts.save(filename)
    playsound(filename)
    os.remove(filename)

# Sample training data
training_data = [
    # Sports-related examples
    ("The football team won the championship with a last-minute goal.", "sports"),
    ("The basketball playoffs are intense this year, with many upsets.", "sports"),
    ("The baseball season is in full swing, with teams competing fiercely.", "sports"),
    ("The tennis player dominated the court, winning in straight sets.", "sports"),
    ("The World Cup is one of the most-watched sporting events globally.", "sports"),
    ("The Olympics bring together athletes from all over the world.", "sports"),
    ("The coach emphasized teamwork and strategy during the game.", "sports"),
    ("The marathon runner set a new world record in the race.", "sports"),
    ("The soccer match ended in a dramatic penalty shootout.", "sports"),
    ("The cricket match was delayed due to rain, but the fans stayed enthusiastic.", "sports"),
    ("The hockey team advanced to the finals after a tough series.", "sports"),
    ("The cycling tour through the mountains was grueling but exhilarating.", "sports"),
    ("The athlete's performance was outstanding, earning them a gold medal.", "sports"),
    ("The rugby match was highly physical, with both teams giving their all.", "sports"),
    ("The swimmer broke the world record in the 100-meter freestyle.", "sports"),
    ("The boxing match ended in a knockout in the third round.", "sports"),
    ("The volleyball team played a close match, winning by just two points.", "sports"),
    ("The golf tournament attracted top players from around the world.", "sports"),
    ("The racing event featured some of the fastest cars on the planet.", "sports"),
    ("The snowboarding competition was thrilling, with high-flying tricks.", "sports"),

    # Politics-related examples
    ("The president delivered a speech on the importance of healthcare reform.", "politics"),
    ("The new bill passed by the Senate focuses on education funding.", "politics"),
    ("The election campaign has been contentious, with both sides making strong arguments.", "politics"),
    ("The government is considering new regulations to address climate change.", "politics"),
    ("The foreign policy debate highlighted differences between the two candidates.", "politics"),
    ("The senator proposed a new tax plan to stimulate economic growth.", "politics"),
    ("The protestors gathered outside the capitol to demand change.", "politics"),
    ("The mayor announced a new initiative to improve public transportation.", "politics"),
    ("The Supreme Court ruling has significant implications for civil rights.", "politics"),
    ("The diplomatic talks aimed at easing tensions between the two nations.", "politics"),
    ("The political landscape is shifting, with new parties gaining popularity.", "politics"),
    ("The candidate's platform focuses on job creation and economic development.", "politics"),
    ("The international summit brought together leaders from around the world.", "politics"),
    ("The congress passed a landmark bill on immigration reform.", "politics"),
    ("The debate on healthcare continues to divide lawmakers.", "politics"),
    ("The governor signed the new education bill into law today.", "politics"),
    ("The policy changes have sparked a national debate on privacy and security.", "politics"),
    ("The administration announced new sanctions against the rogue state.", "politics"),
    ("The political analyst discussed the implications of the recent election.", "politics"),
    ("The House of Representatives voted on the new infrastructure plan.", "politics"),

    # Technology-related examples
    ("The latest smartphone release features cutting-edge technology.", "technology"),
    ("The company announced a breakthrough in artificial intelligence research.", "technology"),
    ("The new software update includes enhanced security features.", "technology"),
    ("The rise of electric vehicles is transforming the automotive industry.", "technology"),
    ("The virtual reality headset offers an immersive gaming experience.", "technology"),
    ("The tech industry is booming, with startups emerging in various sectors.", "technology"),
    ("The innovation in renewable energy technology is driving down costs.", "technology"),
    ("The new app allows users to track their fitness goals more effectively.", "technology"),
    ("The cybersecurity threats have led to increased focus on data protection.", "technology"),
    ("The development of quantum computing could revolutionize various fields.", "technology"),
    ("The social media platform introduced new features to enhance user engagement.", "technology"),
    ("The artificial intelligence chatbot is becoming more human-like in conversations.", "technology"),
    ("The advancements in medical technology are improving patient outcomes.", "technology"),
    ("The drone technology is being used in agriculture to monitor crops.", "technology"),
    ("The wearable tech market is expanding rapidly with new devices.", "technology"),
    ("The blockchain technology is being explored for various applications beyond cryptocurrency.", "technology"),
    ("The tech conference showcased the latest innovations in software and hardware.", "technology"),
    ("The rise of e-commerce has changed the retail landscape dramatically.", "technology"),
    ("The smart home devices are becoming more integrated with each other.", "technology"),
    ("The robotics industry is growing, with robots being used in manufacturing.", "technology"),

    # More Sports-related examples
    ("The gymnasts displayed incredible skill and balance on the apparatus.", "sports"),
    ("The baseball team celebrated a hard-fought victory after extra innings.", "sports"),
    ("The soccer star was transferred to a new team in a record-breaking deal.", "sports"),
    ("The winter sports event attracted athletes from across the globe.", "sports"),
    ("The sports commentator provided in-depth analysis of the match.", "sports"),

    # More Politics-related examples
    ("The senator's speech focused on the need for bipartisan cooperation.", "politics"),
    ("The election results were contested, leading to a recount in several states.", "politics"),
    ("The campaign finance reform has been a hot topic in the recent debates.", "politics"),
    ("The government's new policy aims to reduce carbon emissions.", "politics"),
    ("The trade negotiations between the countries have reached a critical stage.", "politics"),

    # More Technology-related examples
    ("The tech startup received significant venture capital funding for its AI project.", "technology"),
    ("The new operating system is designed to be more user-friendly.", "technology"),
    ("The 3D printing technology is being used to create custom medical implants.", "technology"),
    ("The cloud computing services are becoming more accessible to small businesses.", "technology"),
    ("The tech giant unveiled its plans for a futuristic smart city.", "technology"),
]


# Split data into X (features) and y (labels)
X_train, y_train = zip(*training_data)

# Create a text classification pipeline
model = Pipeline([
    ('vectorizer', TfidfVectorizer()),
    ('classifier', MultinomialNB())
])

# Train the model
model.fit(X_train, y_train)

# Function to capture audio and classify topic
def classify_speech():
    recognizer = sr.Recognizer()

    speak("Please speak about sports, politics, or technology:")
    with sr.Microphone() as source:
        audio = recognizer.listen(source)

        try:
            # Convert speech to text
            text = recognizer.recognize_google(audio)
            print(f"Transcribed Text: {text}")

            # Predict the topic
            topic = model.predict([text])[0]
            print(f"Identified Topic: {topic}")

            # Announce the identified topic
            speak(f"Identified topic: {topic}")

            # Route the user based on the topic
            if topic == "sports":
                speak("Routing to sports prompt...")
                print("Routing to sports prompt...")
                # Add your sports-specific code here
            elif topic == "politics":
                speak("Routing to politics prompt...")
                print("Routing to politics prompt...")
                # Add your politics-specific code here
            elif topic == "technology":
                speak("Routing to technology prompt...")
                print("Routing to technology prompt...")
                # Add your technology-specific code here

        except sr.UnknownValueError:
            print("Sorry, I could not understand your speech.")
            speak("Sorry, I could not understand your speech.")
        except sr.RequestError:
            print("Sorry, I could not request results from the speech recognition service.")
            speak("Sorry, I could not request results from the speech recognition service.")

# Run the application
if __name__ == "__main__":
    classify_speech()
