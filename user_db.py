from flask import Flask, request, render_template_string, jsonify
import sqlite3
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)

# Initialize the OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI model
llm = OpenAI(api_key=openai_api_key)

# Define a prompt template to convert natural language to SQL
template = """
You are an assistant that helps convert natural language queries into SQL queries.

The 'users' table has columns 'first_name', 'last_name', 'age', and 'email'.

Natural Language Query: {query}
SQL Query:
"""

prompt = PromptTemplate(template=template, input_variables=["query"])

# Create the LLMChain using the prompt and the model
chain = LLMChain(prompt=prompt, llm=llm)

# Initialize SQLite database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create a table and insert some sample data
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    ''')
    try:
        cursor.execute('INSERT INTO users (first_name, last_name, age, email) VALUES (?, ?, ?, ?)', ("John", "Doe", 30, "john@example.com"))
        cursor.execute('INSERT INTO users (first_name, last_name, age, email) VALUES (?, ?, ?, ?)', ("Jane", "Doe", 25, "jane@example.com"))
    except sqlite3.IntegrityError:
        print("Sample data already exists. Skipping insertion.")
    conn.commit()
    conn.close()

# Home route with a form for user queries
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        user_query = request.form['query']
        sql_query = chain.run(query=user_query).strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            if sql_query.lower().startswith("select"):
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                conn.close()

                # Convert rows to a list of dictionaries
                result = [dict(row) for row in rows]

                return render_template_string(RESULT_TEMPLATE, query=user_query, sql_query=sql_query, result=result)
            else:
                cursor.execute(sql_query)
                conn.commit()
                conn.close()

                return render_template_string(RESULT_TEMPLATE, query=user_query, sql_query=sql_query, result="Query executed successfully.")
        except sqlite3.Error as e:
            conn.close()
            return render_template_string(RESULT_TEMPLATE, query=user_query, sql_query=sql_query, result=f"Error: {str(e)}")
    return render_template_string(FORM_TEMPLATE)

# Route to list all users in the database
@app.route('/users', methods=['GET'])
def list_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name, age, email FROM users")
    users = cursor.fetchall()
    conn.close()

    # Render the users as an HTML table
    return render_template_string(USERS_TEMPLATE, users=users)

# HTML template for the form
FORM_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Natural Language SQL Interface</title>
</head>
<body>
    <h1>Enter your natural language query:</h1>
    <form method="POST">
        <input type="text" name="query" style="width: 400px;" required>
        <button type="submit">Submit</button>
    </form>
    <br>
    <a href="/users">View all users</a>
</body>
</html>
"""

# HTML template for displaying results
RESULT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Natural Language SQL Interface</title>
</head>
<body>
    <h1>Query: {{ query }}</h1>
    <h2>Generated SQL: {{ sql_query }}</h2>
    {% if result is string %}
        <h3>{{ result }}</h3>
    {% else %}
    <table border="1">
        <tr>
            {% for key in result[0].keys() %}
                <th>{{ key }}</th>
            {% endfor %}
        </tr>
        {% for row in result %}
        <tr>
            {% for value in row.values() %}
                <td>{{ value }}</td>
            {% endfor %}
        </tr>
        {% endfor %}
    </table>
    {% endif %}
    <br>
    <a href="/">Back to Home</a> | <a href="/users">View all users</a>
</body>
</html>
"""

# HTML template for displaying users
USERS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>List of Users</title>
</head>
<body>
    <h1>List of Users</h1>
    <table border="1">
        <tr>
            <th>First Name</th>
            <th>Last Name</th>
            <th>Age</th>
            <th>Email</th>
        </tr>
        {% for user in users %}
        <tr>
            <td>{{ user['first_name'] }}</td>
            <td>{{ user['last_name'] }}</td>
            <td>{{ user['age'] }}</td>
            <td>{{ user['email'] }}</td>
        </tr>
        {% endfor %}
    </table>
    <br>
    <a href="/">Back to Home</a>
</body>
</html>
"""

if __name__ == "__main__":
    # Initialize the database
    init_db()
    # Run the Flask app
    app.run(host="0.0.0.0", port=8080, debug=True)
