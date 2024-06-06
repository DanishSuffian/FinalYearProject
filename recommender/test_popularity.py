from surprise import Dataset, Reader
from mysql.connector import Error
import mysql.connector
import pandas as pd

# Define the database configuration
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
    except Error as e:
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


# Define a reader with the rating scale range. Adjusted to match the dataset's scale
reader = Reader(rating_scale=(1, 5))

# Calculate the popularity of items based on Bayesian average scores
item_stats = interactions.groupby('company_id')['rating'].agg(['count', 'mean'])
C = item_stats['count'].mean()
m = item_stats['mean'].mean()

def bayesian_avg(ratings):
    bayesian_avg = (C * m + ratings.sum()) / (C + ratings.count())
    return round(bayesian_avg, 3)

bayesian_avg_ratings = interactions.groupby('company_id')['rating'].agg(bayesian_avg).reset_index()
bayesian_avg_ratings.columns = ['company_id', 'bayesian_avg']

# Merge with company names
item_stats = item_stats.merge(bayesian_avg_ratings, on='company_id')
item_stats = item_stats.merge(companies[['company_id', 'company_name']])

# Get top recommendations based on popularity (Bayesian average)
top_recommendations = item_stats.sort_values(by='bayesian_avg', ascending=False).head(10)

print(top_recommendations)
