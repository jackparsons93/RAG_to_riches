import requests
from bs4 import BeautifulSoup
from transformers import pipeline

def fetch_wikipedia_article(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    paragraphs = soup.find_all('p')
    
    # Combine all paragraphs into a single text
    article_text = ' '.join([para.get_text() for para in paragraphs])
    return article_text

def chunk_text(text, chunk_size=500):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield ' '.join(words[i:i + chunk_size])

def summarize_text(text):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    summary = ''
    for chunk in chunk_text(text):
        summary_chunk = summarizer(chunk, max_length=150, min_length=40, do_sample=False)[0]['summary_text']
        summary += summary_chunk + ' '
    return summary.strip()

def main(url):
    article_text = fetch_wikipedia_article(url)
    print("Original Article Text:")
    print(article_text[:500])  # Print the first 500 characters of the article
    
    summary = summarize_text(article_text)
    print("\nSummary:")
    print(summary)

if __name__ == "__main__":
    url = input("Enter Wikipedia article URL: ")
    main(url)
