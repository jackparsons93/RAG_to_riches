from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import stripe
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Set the database URI - the name of your SQLite database file
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configure Stripe with the secret key from .env
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Create User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    passcode = db.Column(db.String(10), nullable=True)
    has_paid = db.Column(db.Boolean, default=False)

# Initialize the database
with app.app_context():
    db.create_all()

# Route for the login and registration page
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'login' in request.form:
            # Handle the login
            username = request.form['username']
            password = request.form['password']

            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')

        elif 'register' in request.form:
            # Handle the registration
            username = request.form['username']
            password = request.form['password']

            # Check if the username already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists. Please choose another.', 'danger')
            else:
                # Create a new user and add to the database
                new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
                db.session.add(new_user)
                db.session.commit()
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))

    return render_template('login.html')

# Route for the user dashboard (payment page)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(id=session['user_id']).first()

    if user.has_paid:
        return render_template('dashboard.html', passcode=user.passcode)
    else:
        return render_template('payment.html')

# Route to handle the payment process
@app.route('/pay', methods=['POST'])
def pay():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(id=session['user_id']).first()

    # Create a Stripe Checkout Session
    stripe_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'Premium Passcode',
                },
                'unit_amount': 500,  # $5.00
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=url_for('payment_success', _external=True),
        cancel_url=url_for('dashboard', _external=True),
    )

    return redirect(stripe_session.url)

# Route for successful payment
@app.route('/payment-success')
def payment_success():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(id=session['user_id']).first()

    # Generate a random 4-digit passcode
    user.passcode = str(random.randint(1000, 9999))
    user.has_paid = True
    db.session.commit()

    return redirect(url_for('dashboard'))

# Route for logging out
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
