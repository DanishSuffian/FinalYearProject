import pyrebase
import hashlib
import json
from flask import Flask, render_template, request

config = {
    'apiKey': "AIzaSyB5ZeLFAn2cshEwqsgq6vS3-6MmgdfxgLY",
    'authDomain': "intelintern-f0863.firebaseapp.com",
    'databaseURL': "https://intelintern-f0863-default-rtdb.asia-southeast1.firebasedatabase.app",
    'projectId': "intelintern-f0863",
    'storageBucket': "intelintern-f0863.appspot.com",
    'messagingSenderId': "299592989079",
    'appId': "1:299592989079:web:4a6b5729f3c06c5614ecd2",
    'measurementId': "G-HVC5YL8FYV"
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('login_signup.html')


@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password == confirm_password:
            try:
                username = request.form['username']
                email = request.form['email']
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                new_user = auth.create_user_with_email_and_password(email, hashed_password)
                auth.send_email_verification(new_user['idToken'])

                user_data = {
                    'username': username,
                    'email': email
                }
                db.child('users').push(user_data)

                return json.dumps({'message': 'Signup success'})
            except:
                existing_account = 'This email is already used'
                return json.dumps({'error': existing_account})
    return json.dumps({'error': 'Invalid request'})


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
    app.run(debug=True)
