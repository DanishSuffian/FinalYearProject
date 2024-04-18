import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# Load user-item matrix
user_item_matrix = pd.read_csv('user_item_matrix.csv')

def calculate_cosine_similarity(matrix):
    # Calculate cosine similarity matrix
    similarity_matrix = cosine_similarity(matrix, dense_output=False)
    return similarity_matrix

import numpy as np

def recommend_items(user_id, user_item_matrix, similarity_matrix):
    # Find similar users based on cosine similarity
    similar_users = np.argsort(similarity_matrix[user_id])[::-1]  # Exclude the user itself

    # Get items not interacted by the user
    non_interacted_items = user_item_matrix.loc[user_id][user_item_matrix.loc[user_id] == 0].index.tolist()

    # Recommend items based on similar users' interactions
    recommended_items = []
    for similar_user in similar_users:
        similar_user_items = user_item_matrix.loc[similar_user]
        recommended_items.extend(similar_user_items[similar_user_items > 0].index.tolist())

    recommended_items = list(set(recommended_items) - set(non_interacted_items))[:10]  # Limit to top 10 recommendations

    # Remove 'user_id' from recommended items if present
    recommended_items = [item_id for item_id in recommended_items if item_id != 'user_id']

    return recommended_items




# Example usage
user_id = 2  # Replace with the user ID for recommendations
similarity_matrix = calculate_cosine_similarity(user_item_matrix)
recommended_items = recommend_items(user_id, user_item_matrix, similarity_matrix)
print(f"Recommended items for user {user_id}: {recommended_items}")
