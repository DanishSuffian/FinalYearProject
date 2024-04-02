import pyrebase
import json
import re
import secrets
from flask import Flask, render_template, request, session
from datetime import datetime
from firebase_admin import auth

config = {
    'apiKey': "AIzaSyB5ZeLFAn2cshEwqsgq6vS3-6MmgdfxgLY",
    'authDomain': "intelintern-f0863.firebaseapp.com",
    'databaseURL': "https://intelintern-f0863-default-rtdb.asia-southeast1.firebasedatabase.app",
    'projectId': "intelintern-f0863",
    'storageBucket': "intelintern-f0863.appspot.com",
    'messagingSenderId': "299592989079",
    'appId': "1:299592989079:web:4a6b5729f3c06c5614ecd2",
    'measurementId': "G-HVC5YL8FYV",
    'serviceAccountKey': "credentials/intelintern-f0863-firebase-adminsdk-409yu-21159de1d1.json"
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


@app.route('/')
def index():
    return render_template('landing.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user_query = db.child('users').order_by_child('username').equal_to(username).get()
    if not user_query.each():
        return json.dumps({'error': 'Incorrect username or password'})

    user_data = user_query.each()[0].val()

    try:
        email = user_data['email']

        user = auth.sign_in_with_email_and_password(email, password)
        user_info = auth.get_account_info(user['idToken'])

        if user_info['users'][0]['emailVerified']:
            session['user'] = email
            return json.dumps({'message': 'Login successful'})
        else:
            return json.dumps({'error': 'Email is not verified'})
    except Exception as e:
        print("Error:", e)
        return json.dumps({'error': 'Incorrect username or password'})


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not all([username, email, password, confirm_password]):
            return json.dumps({'error': 'All fields are required'})

        if len(password) < 6:
            return json.dumps({'error': 'Password should be at least 6 characters long'})

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return json.dumps({'error': 'Invalid email format'})

        if password != confirm_password:
            return json.dumps({'error': 'Passwords do not match'})

        try:
            existing_username = db.child('users').order_by_child('username').equal_to(username).get()
            if existing_username.each():
                return json.dumps({'error': 'Username is already taken'})

            existing_email = db.child('users').order_by_child('email').equal_to(email).get()
            if existing_email.each():
                return json.dumps({'error': 'Email address is already taken'})

            new_user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(new_user['idToken'])

            user_data = {
                'username': username,
                'email': email,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            db.child('users').push(user_data)

            return json.dumps({'message': 'Sign up successful'})
        except Exception as e:
            print("Error:", e)
            return json.dumps({'error': 'An error occurred while signing up'})
    else:
        return render_template('login_signup.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
    app.run(debug=True)
