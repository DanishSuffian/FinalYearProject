import pandas as pd
import pickle
from surprise import Dataset, Reader
from surprise import BaselineOnly
from surprise.model_selection import train_test_split


# Function to get top similar items based on item ID
def get_top_similar_items(item_id, top_n=10):
    item_row = similarity_df[similarity_df['item_id'] == item_id]
    if not item_row.empty:
        similarity_scores = eval(item_row['similarity_score'].values[0])
        similar_items = sorted(enumerate(similarity_scores), key=lambda x: x[1], reverse=True)[:top_n]
        top_similar_items = [(similarity_df.iloc[idx]['item_id'], score) for idx, score in similar_items]
        return top_similar_items
    else:
        return []


# Function to get company name from item ID
def get_company_name(item_id):
    if item_id in cf_df['item_id'].values:
        return cf_df[cf_df['item_id'] == item_id]['job_company'].values[0]
    else:
        return 'Unknown'


# Function to calculate weighted recommendations
def get_weighted_recommendations(cf_recommendations, cbf_recommendations, cf_weight, cbf_weight):
    weighted_recommendations = []
    cf_dict = {item_id: score for item_id, score in cf_recommendations}
    cbf_dict = {item_id: score for item_id, score in cbf_recommendations}
    all_items = set(cf_dict.keys()).union(cbf_dict.keys())

    for item_id in all_items:
        cf_score = cf_dict.get(item_id, 0)
        cbf_score = cbf_dict.get(item_id, 0)
        weighted_score = cf_weight * cf_score + cbf_weight * cbf_score
        weighted_recommendations.append((item_id, weighted_score))

    weighted_recommendations.sort(key=lambda x: x[1], reverse=True)
    return weighted_recommendations


# Function to calculate the hit rate
def calculate_hit_rate(hybrid_recommendations, testset):
    hits = 0
    total_users = len(hybrid_recommendations)
    actual_companies = {user_id: item_id for user_id, item_id, rating in testset}

    for user_id, recommendations in hybrid_recommendations.items():
        recommended_items = [item_id for item_id, _ in recommendations]
        actual_item = actual_companies.get(user_id, None)
        if actual_item in recommended_items:
            hits += 1

    hit_rate = hits / total_users
    return hit_rate


def calculate_arhr(hybrid_recommendations, testset):
  total_reciprocal_rank = 0
  total_users = len(hybrid_recommendations)
  actual_companies = {user_id: item_id for user_id, item_id, rating in testset}

  for user_id, recommendations in hybrid_recommendations.items():
    user_reciprocal_rank = 0
    actual_item = actual_companies.get(user_id, None)
    for i, (item_id, _) in enumerate(recommendations):
      if item_id == actual_item:
        user_reciprocal_rank = 1 / (i + 1)
        break  # Assuming recommendations are sorted by descending order
    total_reciprocal_rank += user_reciprocal_rank

  arhr = total_reciprocal_rank / total_users

  return arhr


# Load item similarity scores
similarity_df = pd.read_csv('item_similarity_score.csv')

# Load CF dataset
cf_df = pd.read_csv('item_sentiment_dataset.csv')
reader = Reader(rating_scale=(-2, 2))
cf_data = Dataset.load_from_df(cf_df[['user_id', 'item_id', 'average_sentiment']], reader)

# Split data into training and testing sets
trainset, testset = train_test_split(cf_data, test_size=0.3)

# Train CF model using training set
cf_model = BaselineOnly()
cf_model.fit(trainset)

# Generate CF recommendations for users in the test set
cf_recommendations = {}
for (user_id, item_id, actual_sentiment) in testset:
    if user_id not in cf_recommendations:
        cf_recommendations[user_id] = []
    cf_recommendations[user_id].append((item_id, cf_model.predict(user_id, item_id).est))

# Sort CF recommendations by sentiment scores in descending order for each user
for user_id in cf_recommendations:
    cf_recommendations[user_id].sort(key=lambda x: x[1], reverse=True)

# Generate CBF recommendations using item similarity scores
sample_item = 156
cbf_recommendations = get_top_similar_items(sample_item)

# Normalize CF scores
cf_normalized = {}
for user_id in cf_recommendations:
    cf_scores = [sentiment for _, sentiment in cf_recommendations[user_id]]
    cf_min, cf_max = min(cf_scores), max(cf_scores)
    cf_normalized[user_id] = [(item_id, (sentiment - cf_min) / (cf_max - cf_min)) for item_id, sentiment in
                              cf_recommendations[user_id]]

# Normalize CBF scores
cbf_scores = [score for _, score in cbf_recommendations]
cbf_min, cbf_max = min(cbf_scores), max(cbf_scores)
cbf_normalized = [(item_id, (score - cbf_min) / (cbf_max - cbf_min)) for item_id, score in cbf_recommendations]

# Define weights for CF and CBF recommendations
cf_weight = 0.3
cbf_weight = 0.7

# Generate hybrid recommendations for users in the test set
hybrid_recommendations = {}
for user_id in cf_normalized:
    weighted_recommendations = get_weighted_recommendations(cf_normalized[user_id], cbf_normalized, cf_weight,
                                                            cbf_weight)
    hybrid_recommendations[user_id] = weighted_recommendations

# Save the trained CF model
with open('cf_model.pkl', 'wb') as model_file:
    pickle.dump(cf_model, model_file)

# Calculate and print hit rate
hit_rate = calculate_hit_rate(hybrid_recommendations, testset)
print(f'\nHit Rate: {hit_rate:.2f}')

# Calculate and print hit rate
arhr = calculate_arhr(hybrid_recommendations, testset)
print(f'\nARHR: {arhr:.4f}')
