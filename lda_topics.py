# Required Libraries
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from gensim import corpora
from gensim.models import LdaModel
import pyLDAvis.gensim_models as gensimvis
import pyLDAvis

# Ensure necessary NLTK downloads
nltk.download('punkt')
nltk.download('stopwords')

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

# Convert data into a DataFrame
df = pd.DataFrame(data)

# Text Preprocessing Function
def preprocess(text):
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    text = re.sub(r'\W', ' ', text)   # Remove non-alphabetic characters
    text = text.lower()               # Convert to lowercase
    tokens = word_tokenize(text)      # Tokenize
    stop_words = set(stopwords.words('english'))  # Remove stopwords
    tokens = [word for word in tokens if word not in stop_words]
    return tokens

# Preprocess the dataset
df['cleaned_text'] = df['text'].apply(preprocess)

# Create a dictionary and corpus for LDA
dictionary = corpora.Dictionary(df['cleaned_text'])
corpus = [dictionary.doc2bow(text) for text in df['cleaned_text']]

# Apply Latent Dirichlet Allocation (LDA)
lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=3, passes=10, random_state=100)

# Print out the topics
topics = lda_model.print_topics(num_words=4)
for idx, topic in topics:
    print(f"Topic {idx + 1}: {topic}")

# Visualizing the LDA topics
lda_vis = gensimvis.prepare(lda_model, corpus, dictionary)
pyLDAvis.save_html(lda_vis, 'lda_topics.html')

