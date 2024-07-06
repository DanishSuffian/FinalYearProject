from implicit.als import AlternatingLeastSquares
from sklearn.decomposition import TruncatedSVD, NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
import string
import pandas as pd
import spacy
import mysql.connector

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'intelintern',
    'port': 3306
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            return connection
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None

# Preprocess function for processing text
def preprocess_text(text):
    doc = nlp(text)
    processed_text = []

    for token in doc:
        if token.pos_ != "STOP" and token.text.lower() not in stop_words and token.text.lower() not in punctuation:
            processed_text.append(token.text.lower())

    processed_text = " ".join(processed_text)
    return processed_text

# Initialize spaCy and NLTK stopwords
nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words('english'))
punctuation = set(string.punctuation)

# Fetch data from MySQL
connection = get_db_connection()
if connection:
    try:
        query_interactions = "SELECT * FROM interactions"
        interactions = pd.read_sql(query_interactions, connection)
        query_companies = "SELECT * FROM companies"
        companies = pd.read_sql(query_companies, connection)
    except mysql.connector.Error as e:
        print(f"Error reading data from MySQL: {e}")
    finally:
        connection.close()

# Combine relevant text columns into a single text column 'combined_text'
companies['combined_text'] = companies['company_name'] + ' ' + companies['company_location'] + ' ' + companies['company_type'] + ' ' + companies['company_scope']
companies['combined_text'] = companies['combined_text'].fillna('')

# Apply preprocessing to 'combined_text' column
companies['combined_text'] = companies['combined_text'].apply(preprocess_text)

# Initialize TF-IDF vectorizer and fit-transform the text
tfidf_vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf_vectorizer.fit_transform(companies['combined_text'])

# Initialize Truncated SVD, NMF, and ALS models
n_components = 10
svd = TruncatedSVD(n_components=n_components)
nmf = NMF(n_components=n_components, init='random', random_state=0)
als = AlternatingLeastSquares()

# Fit-transform TF-IDF matrix using Truncated SVD, NMF, and ALS
tfidf_matrix_svd = svd.fit_transform(tfidf_matrix)
tfidf_matrix_nmf = nmf.fit_transform(tfidf_matrix)
als.fit(tfidf_matrix.T)
item_factors = als.item_factors

# Compute cosine similarity matrix for Truncated SVD, NMF, and ALS
cosine_sim_matrix_tfidf = cosine_similarity(tfidf_matrix, tfidf_matrix)
cosine_sim_matrix_svd = cosine_similarity(tfidf_matrix_svd, tfidf_matrix_svd)
cosine_sim_matrix_nmf = cosine_similarity(tfidf_matrix_nmf, tfidf_matrix_nmf)
cosine_sim_matrix_als = cosine_similarity(item_factors, item_factors)

# Evaluate relevance based on feature similarity
def evaluate_relevance(user_last_interacted, recommendations, features, relevance_threshold):
    total_relevant = 0
    total_recommendations = 0
    relevant_items = []
    non_relevant_items = []

    if user_last_interacted.empty:
        return 0, relevant_items, non_relevant_items

    interacted_company_id = user_last_interacted.iloc[0]['company_id']
    interacted_company = companies[companies['company_id'] == interacted_company_id]

    if interacted_company.empty:
        return 0, relevant_items, non_relevant_items

    for recommended_company_id in recommendations:
        recommended_company = companies[companies['company_id'] == recommended_company_id]
        if recommended_company.empty:
            continue

        match_count = 0
        for feature in features:
            if interacted_company.iloc[0][feature] == recommended_company.iloc[0][feature]:
                match_count += 1
        if match_count >= relevance_threshold:
            total_relevant += 1
            relevant_items.append(recommended_company_id)
        else:
            non_relevant_items.append(recommended_company_id)
        total_recommendations += 1

    return total_relevant / total_recommendations if total_recommendations > 0 else 0, relevant_items, non_relevant_items

# Get recommendations
def get_cbf_recommendations(user_id, similarity_matrix, num_recommendations=10):
    user_interactions = interactions[interactions['user_id'] == user_id]
    if user_interactions.empty:
        return [], 0, [], []

    user_last_interacted = user_interactions.iloc[-1:]
    interacted_company_id = user_last_interacted.iloc[0]['company_id']
    interacted_company_index = companies[companies['company_id'] == interacted_company_id].index[0]

    similarity_scores = similarity_matrix[interacted_company_index]
    recommended_company_indices = similarity_scores.argsort()[-num_recommendations:][::-1]
    recommended_company_ids = companies.iloc[recommended_company_indices]['company_id'].values

    # Define features to match and relevance threshold
    features_to_match = ['company_location', 'company_scope', 'company_type']
    RELEVANCE_THRESHOLD = 2

    relevance_percentage, relevant_items, non_relevant_items = evaluate_relevance(user_last_interacted,
                                                                                  recommended_company_ids,
                                                                                  features_to_match,
                                                                                  RELEVANCE_THRESHOLD)
    return recommended_company_ids, relevance_percentage, relevant_items, non_relevant_items

# Evaluate recommendations for each algorithm
def evaluate_cbf_algorithm(user_id, similarity_matrix, num_recommendations=10):
    recommended_company_ids, relevance_percentage, relevant_items, non_relevant_items = get_cbf_recommendations(user_id,
                                                                                                                 similarity_matrix,
                                                                                                                 num_recommendations)

    tp = len(relevant_items)
    fp = len(non_relevant_items)
    fn = num_recommendations - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return precision, recall, f1

# Calculate average metrics for CBF
def calculate_average_metrics_cbf(testset, similarity_matrix, num_recommendations=10):
    total_precision = 0
    total_recall = 0
    total_f1 = 0
    user_ids = set(testset['user_id'])

    for user_id in user_ids:
        precision, recall, f1 = evaluate_cbf_algorithm(user_id, similarity_matrix, num_recommendations)
        total_precision += precision
        total_recall += recall
        total_f1 += f1

    count = len(user_ids)
    avg_precision = total_precision / count if count > 0 else 0
    avg_recall = total_recall / count if count > 0 else 0
    avg_f1 = total_f1 / count if count > 0 else 0

    return avg_precision, avg_recall, avg_f1

# Define testset
testset = interactions.groupby('user_id').last().reset_index()[['user_id', 'company_id']]

# Iterate over similarity matrices and calculate metrics
similarity_matrices = {
    'TF-IDF': cosine_sim_matrix_tfidf,
    'SVD': cosine_sim_matrix_svd,
    'NMF': cosine_sim_matrix_nmf,
    'ALS': cosine_sim_matrix_als
}

for sim_name, sim_matrix in similarity_matrices.items():
    avg_precision, avg_recall, avg_f1 = calculate_average_metrics_cbf(testset, sim_matrix)
    print(f"\n{sim_name} Results:")
    print(f"Average Precision on the test set: {avg_precision:.2f}")
    print(f"Average Recall on the test set: {avg_recall:.2f}")
    print(f"Average F1-score on the test set: {avg_f1:.2f}")
