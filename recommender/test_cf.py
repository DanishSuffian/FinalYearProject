from surprise import Dataset, Reader
from surprise import SVD, NMF, SlopeOne, BaselineOnly
from surprise.model_selection import cross_validate
from mysql.connector import Error
import pandas as pd
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
    except Error as e:
        print(f"Error: {e}")
        return None


connection = get_db_connection()
if connection:
    try:
        query = "SELECT user_id, company_id, rating FROM interactions"
        df = pd.read_sql(query, connection)
    except mysql.connector.Error as e:
        print(f"Error reading data from MySQL: {e}")
    finally:
        connection.close()

# Function to normalize sentiment scores from -2 to 2 to 1 to 5
# def normalize_sentiment(score):
#    x_min = -2
#    x_max = 2
#    y_min = 1
#    y_max = 5
#    return ((score - x_min) / (x_max - x_min)) * (y_max - y_min) + y_min


# Apply normalization to the sentiment_score column
# df['sentiment_score'] = df['sentiment_score'].apply(normalize_sentiment)

# Define a reader with the rating scale range. Adjusted to match the dataset's scale
reader = Reader(rating_scale=(1, 5))

# Load the data into the Surprise dataset format
data = Dataset.load_from_df(df[['user_id', 'company_id', 'rating']], reader)  # Adjusted column name

# List of algorithms to be evaluated
algorithms = [
    ('Baseline', BaselineOnly()),
    ('SVD', SVD()),
    ('NMF', NMF()),
    ('SlopeOne', SlopeOne()),
]

# Metrics to be used for evaluation
metrics = ['rmse', 'mae']

# Loop through each algorithm and perform cross-validation
for alg_name, algo in algorithms:
    print(f'Running {alg_name}...')

    # Perform 5, 10 or 15-fold cross-validation for the current algorithm
    results = cross_validate(algo, data, measures=metrics, cv=15, verbose=True)

    print(f'{alg_name} Results:')
    print(f"Average RMSE: {results['test_rmse'].mean()}")
    print(f"Average MAE: {results['test_mae'].mean()}")
    print()
