from surprise import Dataset, Reader, SVD, BaselineOnly, NMF, SlopeOne
from surprise.model_selection import train_test_split
import pandas as pd
import mysql.connector

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

# Initialize Surprise Reader and Dataset
reader = Reader(rating_scale=(1, 5))
data = Dataset.load_from_df(interactions[['user_id', 'company_id', 'rating']], reader)
trainset, testset = train_test_split(data, test_size=0.2)

from surprise import Dataset, Reader, SVD, BaselineOnly, NMF, SlopeOne

# List of algorithms to test
algorithms = {
    'Baseline': BaselineOnly(),
    'SVD': SVD(),
    'NMF': NMF(),
    'SlopeOne': SlopeOne()
}

# Evaluate relevance based on last interacted company and feature similarity
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
def get_cf_recommendations(user_id, algo, num_recommendations=10):
    user_interactions = interactions[interactions['user_id'] == user_id]
    if user_interactions.empty:
        return [], 0, [], []

    user_last_interacted = user_interactions.iloc[-1:]
    recommendations = algo.test(testset)
    recommended_company_ids = [rec.iid for rec in recommendations if rec.uid == user_id]

    # Define features to match and relevance threshold
    features_to_match = ['company_location', 'company_scope', 'company_type']
    RELEVANCE_THRESHOLD = 2

    relevance_percentage, relevant_items, non_relevant_items = evaluate_relevance(user_last_interacted,
                                                                                  recommended_company_ids[:num_recommendations],
                                                                                  features_to_match,
                                                                                  RELEVANCE_THRESHOLD)
    return recommended_company_ids[:num_recommendations], relevance_percentage, relevant_items, non_relevant_items

# Calculate precision, recall, and F1-score for a user
def calculate_precision_recall_f1(user_id, algo, num_recommendations=10):
    recommendations, relevance_percentage, relevant_items, non_relevant_items = get_cf_recommendations(user_id,
                                                                                                           algo,
                                                                                                           num_recommendations)

    tp = len(relevant_items)
    fp = len(non_relevant_items)
    fn = num_recommendations - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return precision, recall, f1

# Calculate average metrics on test set
def calculate_average_metrics(testset, algo, num_recommendations=10):
    total_precision = 0
    total_recall = 0
    total_f1 = 0
    user_ids = set([uid for uid, _, _ in testset])

    for user_id in user_ids:
        precision, recall, f1 = calculate_precision_recall_f1(user_id, algo, num_recommendations)
        total_precision += precision
        total_recall += recall
        total_f1 += f1

    count = len(user_ids)
    avg_precision = total_precision / count if count > 0 else 0
    avg_recall = total_recall / count if count > 0 else 0
    avg_f1 = total_f1 / count if count > 0 else 0

    return avg_precision, avg_recall, avg_f1

# Iterate over algorithms and calculate metrics
for algo_name, algo in algorithms.items():
    algo.fit(trainset)
    avg_precision, avg_recall, avg_f1 = calculate_average_metrics(testset, algo)
    print(f"\n{algo_name} Results:")
    print(f"Average Precision on the test set: {avg_precision:.2f}")
    print(f"Average Recall on the test set: {avg_recall:.2f}")
    print(f"Average F1-score on the test set: {avg_f1:.2f}")
