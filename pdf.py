import pdfplumber
from openai import OpenAI
from reportlab.lib import utils
import PyPDF2
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

client = OpenAI(api_key='YOUR_API_KEY_HERE')
# Open the PDF file
with pdfplumber.open('theory.pdf') as pdf:
    # Iterate over each page
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text()
        print(f"Page {page_num + 1}:\n{text}\n")


# Load your OpenAI API key

# Function to extract text and identify questions
def extract_questions(pdf_file):
    with open(pdf_file, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        num_pages = len(reader.pages)

        questions = []
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            text = page.extract_text()

            # Use a regex pattern to find questions
            found_questions = re.findall(r'.*?\?', text)
            questions.extend(found_questions)

    return questions

# Extract questions from the PDF
pdf_file = 'theory.pdf'
questions = extract_questions(pdf_file)

def ask_openai(question):
    response = client.chat.completions.create(model="gpt-3.5-turbo", 
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": question}
    ])
    answer = response.choices[0].message.content
    return answer

# Iterate over questions and get answers
for question in questions:
    print(f"Question: {question}")
    answer = ask_openai(question)
    print(f"Answer: {answer}\n")



def save_answers_to_pdf(questions_answers, output_pdf):
    c = canvas.Canvas(output_pdf, pagesize=letter)
    width, height = letter
    
    # Constants
    x_margin = 50
    y_position = height - 50  # Start near the top of the page
    line_height = 14  # Height of each line of text
    max_line_width = width - 2 * x_margin  # Maximum width of the line

    def draw_wrapped_text(c, text, x, y):
        """Draw text with automatic wrapping"""
        wrapped_text = utils.simpleSplit(text, c._fontname, c._fontsize, max_line_width)
        for line in wrapped_text:
            c.drawString(x, y, line)
            y -= line_height
            if y < 2 * line_height:  # Check if we need a new page
                c.showPage()
                y = height - 50
        return y
    
    for question, answer in questions_answers:
        # Draw the question
        y_position = draw_wrapped_text(c, f"Question: {question}", x_margin, y_position)
        
        # Add space between question and answer
        y_position -= line_height
        
        # Draw the answer
        lines = answer.splitlines()
        for line in lines:
            y_position = draw_wrapped_text(c, line, x_margin, y_position)
            y_position -= line_height  # Space between lines

        # Add additional space between Q&A pairs
        y_position -= line_height

    c.save()

# Example: Save to PDF
questions_answers = [(q, ask_openai(q)) for q in questions]
save_answers_to_pdf(questions_answers, "answers_output.pdf")


