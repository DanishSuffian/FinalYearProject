import spacy
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import mysql.connector
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split

# Global relevance threshold
RELEVANCE_THRESHOLD = 2

# Initialize spaCy
nlp = spacy.load("en_core_web_sm")
stop_words = spacy.lang.en.stop_words.STOP_WORDS
punctuation = string.punctuation


# Preprocess text function
def preprocess_text(text):
    doc = nlp(text)
    processed_text = [token.text.lower() for token in doc if
                      token.pos_ != "STOP" and token.text.lower() not in stop_words and token.text.lower() not in punctuation]
    return " ".join(processed_text)


# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'intelintern',
    'port': 3306
}


# Get database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            return connection
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None


# Fetch data
connection = get_db_connection()
if connection:
    try:
        query_users = "SELECT * FROM users"
        users = pd.read_sql(query_users, connection)
        query_companies = "SELECT * FROM companies"
        companies = pd.read_sql(query_companies, connection)
        query_interactions = "SELECT * FROM interactions"
        interactions = pd.read_sql(query_interactions, connection)
    except mysql.connector.Error as e:
        print(f"Error reading data from MySQL: {e}")
    finally:
        connection.close()

# Preprocess company data for CBF
companies['content'] = companies['company_name'] + ' ' + companies['company_location'] + ' ' + companies[
    'company_type'] + ' ' + companies['company_scope']
companies['content'] = companies['content'].fillna('')
companies['content'] = companies['content'].apply(preprocess_text)

tfidf_vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf_vectorizer.fit_transform(companies['content'])

svd = TruncatedSVD(n_components=10)
tfidf_svd = svd.fit_transform(tfidf_matrix)


# Normalize sentiment scores for CF
def normalize_sentiment(score):
    x_min = -2
    x_max = 2
    y_min = 1
    y_max = 5
    return ((score - x_min) / (x_max - x_min)) * (y_max - y_min) + y_min


interactions['sentiment_score'] = interactions['sentiment_score'].apply(normalize_sentiment)

reader = Reader(rating_scale=(1, 5))
data = Dataset.load_from_df(interactions[['user_id', 'company_id', 'sentiment_score']], reader)
trainset, testset = train_test_split(data, test_size=0.2)

algo = SVD()
algo.fit(trainset)

features_to_match = ['company_location', 'company_scope', 'company_type']


# Hybrid recommendation function
def get_hybrid_recommendations(user_id, num_recommendations=10):
    user_interactions = interactions[interactions['user_id'] == user_id]
    if user_interactions.empty:
        return [], [], [], 0, [], []

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

    # Normalize scores
    max_cbf_score = max(cbf_recommendations, key=lambda x: x[1])[1]
    max_cf_score = max(cf_recommendations, key=lambda x: x[1])[1]
    min_cbf_score = min(cbf_recommendations, key=lambda x: x[1])[1]
    min_cf_score = min(cf_recommendations, key=lambda x: x[1])[1]

    cbf_recommendations = [(company_id, (score - min_cbf_score) / (max_cbf_score - min_cbf_score)) for company_id, score
                           in cbf_recommendations]
    cf_recommendations = [(company_id, (score - min_cf_score) / (max_cf_score - min_cf_score)) for company_id, score in
                          cf_recommendations]

    # Combine recommendations with weights
    weighted_hybrid_recommendations = {}
    for company_id, cbf_score in cbf_recommendations:
        weighted_hybrid_recommendations[company_id] = weighted_hybrid_recommendations.get(company_id,
                                                                                          0) + 0.7 * cbf_score

    for company_id, cf_score in cf_recommendations:
        weighted_hybrid_recommendations[company_id] = weighted_hybrid_recommendations.get(company_id,
                                                                                          0) + 0.3 * cf_score

    # Sort the combined recommendations based on weights and remove duplicates
    weighted_hybrid_recommendations = sorted(weighted_hybrid_recommendations.items(), key=lambda x: x[1], reverse=True)
    weighted_hybrid_recommendations = [rec[0] for rec in weighted_hybrid_recommendations]

    # Evaluate relevance based on feature matching
    relevance_percentage, relevant_items, non_relevant_items = evaluate_relevance(user_interactions,
                                                                                  weighted_hybrid_recommendations[
                                                                                  :num_recommendations],
                                                                                  features_to_match,
                                                                                  RELEVANCE_THRESHOLD)

    return weighted_hybrid_recommendations[:num_recommendations], cbf_recommendations[
                                                                  :num_recommendations], cf_recommendations[
                                                                                         :num_recommendations], relevance_percentage, relevant_items, non_relevant_items


# Define function to evaluate relevance based on feature matching
def evaluate_relevance(user_interactions, recommendations, features, relevance_threshold=RELEVANCE_THRESHOLD):
    total_relevant = 0
    total_recommendations = 0
    relevant_items = []
    non_relevant_items = []

    for _, interacted_interaction in user_interactions.iterrows():  # Iterate over DataFrame rows
        interacted_company_id = interacted_interaction['company_id']
        interacted_company = companies[companies['company_id'] == interacted_company_id]

        if interacted_company.empty:
            continue  # Skip if interacted company not found

        for recommended_company_id in recommendations:
            recommended_company = companies[companies['company_id'] == recommended_company_id]
            if recommended_company.empty:
                continue  # Skip if recommended company not found

            match_count = 0
            for feature in features:
                if interacted_company.iloc[0][feature] == recommended_company.iloc[0][feature]:
                    match_count += 1
            if match_count >= relevance_threshold:
                total_relevant += 1
                relevant_items.append(recommended_company_id)
            else:
                non_relevant_items.append(recommended_company_id)
        total_recommendations += len(recommendations)

    return total_relevant / total_recommendations if total_recommendations > 0 else 0, relevant_items, non_relevant_items


# Calculate precision, recall, and F1-score for a user
def calculate_precision_recall_f1(user_id, num_recommendations=10):
    _, _, _, _, relevant_items, non_relevant_items = get_hybrid_recommendations(user_id, num_recommendations)

    tp = len(relevant_items)
    fp = len(non_relevant_items)
    fn = interactions[(interactions['user_id'] == user_id) & (~interactions['company_id'].isin(relevant_items))].shape[
        0]

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return precision, recall, f1


# Calculate average precision, recall, and F1-score for the test set
def calculate_average_metrics(testset, num_recommendations=10):
    user_ids = set([interaction[0] for interaction in testset])
    total_precision = 0
    total_recall = 0
    total_f1 = 0
    count = 0

    for user_id in user_ids:
        precision, recall, f1 = calculate_precision_recall_f1(user_id, num_recommendations)
        total_precision += precision
        total_recall += recall
        total_f1 += f1
        count += 1

    avg_precision = total_precision / count if count > 0 else 0
    avg_recall = total_recall / count if count > 0 else 0
    avg_f1 = total_f1 / count if count > 0 else 0

    return avg_precision, avg_recall, avg_f1


# Example usage:
precision, recall, f1 = calculate_precision_recall_f1(1)
print(f"Precision: {precision:.2f}, Recall: {recall:.2f}, F1-score: {f1:.2f}")

# Get average metrics on test set
avg_precision, avg_recall, avg_f1 = calculate_average_metrics(testset)
print(f"\nAverage Precision on the test set: {avg_precision:.2f}")
print(f"Average Recall on the test set: {avg_recall:.2f}")
print(f"Average F1-score on the test set: {avg_f1:.2f}")
