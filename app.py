import json
import re
import secrets
from datetime import datetime

import bcrypt
import pandas as pd

import mysql.connector
from mysql.connector import Error
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
import string
import spacy
from surprise import SVD, Reader, Dataset

from flask import Flask, render_template, request, session, jsonify

app = Flask(__name__)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'intelintern',
    'port': 3306
}

app.secret_key = secrets.token_hex(16)

nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words('english'))
punctuation = set(string.punctuation)


def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None


def preprocess_text(text):
    doc = nlp(text)
    processed_text = []

    for token in doc:
        if token.pos_ != "STOP" and token.text.lower() not in stop_words and token.text.lower() not in punctuation:
            processed_text.append(token.text.lower())

    processed_text = " ".join(processed_text)
    return processed_text


connection = get_db_connection()
if connection:
    try:
        query_users = "SELECT * FROM users"
        users = pd.read_sql(query_users, connection)
        query_companies = "SELECT * FROM companies"
        companies = pd.read_sql(query_companies, connection)
        query_interactions = "SELECT * FROM interactions "
        interactions = pd.read_sql(query_interactions, connection)
    except mysql.connector.Error as e:
        print(f"Error reading data from MySQL: {e}")
    finally:
        connection.close()

companies['content'] = companies['company_name'] + ' ' + companies['company_location'] + ' ' + companies[
    'company_type'] + ' ' + companies['company_scope']
companies['content'] = companies['content'].fillna('')
companies['content'] = companies['content'].apply(preprocess_text)

tfidf_vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf_vectorizer.fit_transform(companies['content'])

svd = TruncatedSVD(n_components=10)
tfidf_svd = svd.fit_transform(tfidf_matrix)

# Calculate the popularity of items based on Bayesian average scores
item_stats = interactions.groupby('company_id')['rating'].agg(['count', 'mean'])
C = item_stats['count'].mean()
m = item_stats['mean'].mean()


def bayesian_avg(ratings):
    bayesian_avg = (C * m + ratings.sum()) / (C + ratings.count())
    return round(bayesian_avg, 3)


def normalize_sentiment(score):
    x_min = -2
    x_max = 2
    y_min = 1
    y_max = 5
    return ((score - x_min) / (x_max - x_min)) * (y_max - y_min) + y_min


interactions['sentiment_score'] = interactions['sentiment_score'].apply(normalize_sentiment)

reader = Reader(rating_scale=(1, 5))

data = Dataset.load_from_df(interactions[['user_id', 'company_id', 'sentiment_score']], reader)

# Split the data into training and testing sets
trainset = data.build_full_trainset()

# Initialize the SVD algorithm and fit it to the training set
algo = SVD()
algo.fit(trainset)

features_to_match = ['company_location', 'company_scope', 'company_type']


def get_hybrid_recommendations(user_id, num_recommendations=10):
    connection = get_db_connection()
    if not connection:
        return [], [], []

    try:
        interactions = pd.read_sql("SELECT * FROM interactions", connection)

        user_interactions = interactions[interactions['user_id'] == user_id]
        if user_interactions.empty:
            bayesian_avg_ratings = interactions.groupby('company_id')['rating'].agg(bayesian_avg).reset_index()
            bayesian_avg_ratings.columns = ['company_id', 'bayesian_avg']
            bayesian_avg_ratings = bayesian_avg_ratings.merge(companies[['company_id', 'company_name']],
                                                              on='company_id')
            top_recommendations = bayesian_avg_ratings.sort_values(by='bayesian_avg', ascending=False).head(
                num_recommendations)
            return list(top_recommendations['company_id']), list(top_recommendations['bayesian_avg']), []

        last_company_id = user_interactions['company_id'].iloc[-1]
        company_index = companies[companies['company_id'] == last_company_id].index[0]
        company_vector = tfidf_svd[company_index].reshape(1, -1)
        similarity_scores = cosine_similarity(company_vector, tfidf_svd)[0]

        cbf_recommendations = sorted(list(enumerate(similarity_scores)), key=lambda x: x[1], reverse=True)[
                              1:num_recommendations + 1]
        cbf_recommendations = [(companies.iloc[i[0]]['company_id'], i[1]) for i in cbf_recommendations]

        all_company_ids = companies['company_id'].tolist()
        cf_recommendations = [(company_id, algo.predict(user_id, company_id).est) for company_id in all_company_ids]
        cf_recommendations = sorted(cf_recommendations, key=lambda x: x[1], reverse=True)[:num_recommendations]

        max_cbf_score = max(cbf_recommendations, key=lambda x: x[1])[1]
        max_cf_score = max(cf_recommendations, key=lambda x: x[1])[1]
        min_cbf_score = min(cbf_recommendations, key=lambda x: x[1])[1]
        min_cf_score = min(cf_recommendations, key=lambda x: x[1])[1]

        cbf_recommendations = [(company_id, (score - min_cbf_score) / (max_cbf_score - min_cbf_score)) for
                               company_id, score in cbf_recommendations]
        cf_recommendations = [(company_id, (score - min_cf_score) / (max_cf_score - min_cf_score)) for company_id, score
                              in cf_recommendations]

        weighted_hybrid_recommendations = {}
        for company_id, cbf_score in cbf_recommendations:
            weighted_hybrid_recommendations[company_id] = weighted_hybrid_recommendations.get(company_id,
                                                                                              0) + 0.7 * cbf_score

        for company_id, cf_score in cf_recommendations:
            weighted_hybrid_recommendations[company_id] = weighted_hybrid_recommendations.get(company_id,
                                                                                              0) + 0.3 * cf_score

        weighted_hybrid_recommendations = sorted(weighted_hybrid_recommendations.items(), key=lambda x: x[1],
                                                 reverse=True)
        weighted_hybrid_recommendations = [rec[0] for rec in weighted_hybrid_recommendations]

        return weighted_hybrid_recommendations[:num_recommendations], cbf_recommendations[
                                                                      :num_recommendations], cf_recommendations[
                                                                                             :num_recommendations]
    finally:
        connection.close()



@app.route('/')
def index():
    return render_template('landing.html')


# --------------------------------------Login and Signup--------------------------------------

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if not all([username, password]):
        return json.dumps({'error': 'All fields are required'})

    connection = get_db_connection()
    if not connection:
        return json.dumps({'error': 'Database connection failed'})

    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    # Check if the user exists
    if user:
        # Check for admin credentials
        if username == 'admin' and password == 'admin123':
            session['user_id'] = user['user_id']
            return json.dumps({'message': 'Login successful'})

        # Check hashed password for regular users
        if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id'] = user['user_id']
            return json.dumps({'message': 'Login successful'})
        else:
            return json.dumps({'error': 'Incorrect username or password'})
    else:
        return json.dumps({'error': 'Incorrect username or password'})

    # if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
    #     session['user_id'] = user['user_id']
    #     return json.dumps({'message': 'Login successful'})
    # else:
    #     return json.dumps({'error': 'Incorrect username or password'})


@app.route('/signup', methods=['GET'])
def show_signup_form():
    return render_template('login_signup.html')


@app.route('/signup', methods=['POST'])
def signup():
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

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    connection = get_db_connection()
    if not connection:
        return json.dumps({'error': 'Database connection failed'})

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.close()
        connection.close()
        return json.dumps({'error': 'Username is already taken'})

    cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
    connection.commit()
    cursor.close()
    connection.close()

    return json.dumps({'message': 'Sign up successful'})


# -----------------------------------------Dashboard------------------------------------------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return render_template('login_signup.html', error='User not logged in.')

    user_id = session['user_id']
    connection = get_db_connection()
    if not connection:
        return render_template('dashboard.html', error='Database connection failed.')

    try:
        hybrid_recommendations, _, _ = get_hybrid_recommendations(user_id)

        if not hybrid_recommendations:
            return render_template('dashboard.html', error='No recommendations available.')

        recommended_companies = []
        cursor = connection.cursor(dictionary=True)
        for company_id in hybrid_recommendations:
            cursor.execute("""
                SELECT 
                    c.company_id,
                    c.company_name,
                    c.company_location,
                    c.company_type,
                    c.company_scope,
                    c.company_image,
                    c.company_link,
                    (SELECT COUNT(*) FROM interactions WHERE company_id = c.company_id) AS review_count
                FROM 
                    companies c 
                WHERE
                    c.company_id = %s
            """, (int(company_id),))
            result = cursor.fetchone()
            if result:
                recommended_companies.append(result)
        cursor.close()

        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM interactions WHERE user_id = %s", (user_id,))
        interaction_count = cursor.fetchone()[0]
        cursor.close()

        if interaction_count == 0:
            cursor = connection.cursor()
            cursor.execute("SELECT DISTINCT company_location FROM companies")
            locations = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT company_type FROM companies")
            types = [row[0] for row in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT company_scope FROM companies")
            scopes = [row[0] for row in cursor.fetchall()]

            return render_template('dashboard.html', show_multiform=True, recommendations=recommended_companies,
                                   locations=locations, types=types, scopes=scopes)
        return render_template('dashboard.html', recommendations=recommended_companies)
    except mysql.connector.Error as e:
        return render_template('dashboard.html', error=f'Error reading data from MySQL: {e}')
    finally:
        connection.close()


@app.route('/get_counts', methods=['GET'])
def get_counts():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM companies")
            company_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM interactions WHERE pros IS NOT NULL AND cons IS NOT NULL")
            review_count = cursor.fetchone()[0]

            return jsonify({
                'user_count': user_count,
                'company_count': company_count,
                'review_count': review_count
            })
        except mysql.connector.Error as e:
            print(f"Error reading data from MySQL: {e}")
            return json.dumps({'error': str(e)}), 500
        finally:
            connection.close()
    else:
        return json.dumps({'error': 'Failed to connect to the database'}), 500


@app.route('/search')
def search():
    query = request.args.get('query')
    connection = get_db_connection()
    if not connection:
        return render_template('search_results.html', companies=[])

    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT * FROM companies WHERE MATCH(company_name, company_location, company_type, company_scope) AGAINST(%s);

        """, (query,))
        companies = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return render_template('search_results.html', companies=companies)


@app.route('/autocomplete-options')
def autocomplete_options():
    query = request.args.get('query')
    if not query:
        return jsonify([])

    autocomplete_options = []
    for column in ['company_name', 'company_location', 'company_type', 'company_scope']:
        autocomplete_options.extend(companies[column].unique().tolist())

    matched_options = []
    for option in autocomplete_options:
        words = option.split()
        if any(word.lower().startswith(query.lower()) for word in words):
            matched_options.append(option)
    return jsonify(matched_options[:10])  # Limit to 10 autocomplete options


# --------------------------------------Preferences Form--------------------------------------
@app.route('/generate_recommendations', methods=['POST'])
def generate_recommendations():
    try:
        location = request.json.get('location')
        type = request.json.get('type')
        scope = request.json.get('scope')
        dream_company_description = request.json.get('company_description')

        user_input = f"{dream_company_description} {location} {type} {scope}"
        user_input = preprocess_text(user_input)

        user_vector = tfidf_vectorizer.transform([user_input])
        user_vector_svd = svd.transform(user_vector)

        similarity_scores = cosine_similarity(user_vector_svd, tfidf_svd)[0]

        num_recommendations = 3
        cbf_recommendations = sorted(list(enumerate(similarity_scores)), key=lambda x: x[1], reverse=True)[
                              :num_recommendations]
        cbf_recommendations = [(company_id + 1, score) for company_id, score in
                               cbf_recommendations]

        recommendations = []
        for company_id, score in cbf_recommendations:
            print(f'Company ID: {company_id}')

            if company_id in companies['company_id'].values:
                company = companies[companies['company_id'] == company_id].iloc[0]
                recommendations.append({
                    'company_id': company_id,
                    'company_name': company['company_name'],
                    'company_location': company['company_location'],
                    'company_type': company['company_type'],
                    'similarity_score': score
                })
            else:
                print(f'Company ID {company_id} not found in companies DataFrame')

        return jsonify({'recommendations': recommendations})

    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/submit_interaction', methods=['POST'])
def submit_interaction():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    user_id = session['user_id']
    selected_companies = request.form.getlist('company')

    # Debug print to check received data
    print(f"Received user_id: {user_id}, companies: {selected_companies}")

    # Check if selected_companies is received as a list
    if not isinstance(selected_companies, list):
        return jsonify({'error': 'Invalid data format for companies'}), 400

    # Save the user's first interaction in the database
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor()
        interaction_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for company_id in selected_companies:
            cursor.execute("INSERT INTO interactions (user_id, company_id, interaction_date) VALUES (%s, %s, %s)",
                           (user_id, company_id, interaction_date))
        connection.commit()
        cursor.close()
        return jsonify({'message': 'Preferences Saved'})
    except mysql.connector.Error as e:
        print(f"Database error: {e}")  # Debug print for database errors
        return jsonify({'error': f'Database error: {e}'}), 500
    finally:
        connection.close()
# --------------------------------------------------------------------------------------------


# --------------------------------------------Saved-------------------------------------------
@app.route('/saved')
def saved():
    return render_template('saved.html')
# --------------------------------------------------------------------------------------------


# -------------------------------------------Account------------------------------------------
@app.route('/account')
def account():
    return render_template('account.html')
# --------------------------------------------------------------------------------------------


# -------------------------------------------Logout-------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return render_template('login_signup.html')
# --------------------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)
