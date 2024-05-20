import pandas as pd
from surprise import Dataset, Reader
from surprise import SVD, NMF, SlopeOne, BaselineOnly
from surprise.model_selection import cross_validate

# Load the dataset from a CSV file
df = pd.read_csv('item_sentiment_dataset.csv')

# Define a reader with the rating scale range. Adjusted to match the dataset's scale
reader = Reader(rating_scale=(-2, 2))

# Load the data into the Surprise dataset format
data = Dataset.load_from_df(df[['user_id', 'item_id', 'average_sentiment']], reader)

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
    results = cross_validate(algo, data, measures=metrics, cv=5, verbose=True)

    # Output the results for the current algorithm
    print(f'{alg_name} Results:')
    for metric, values in results.items():
        if metric.startswith('test_'):
            metric_name = metric.replace('test_', '').upper()
            avg_score = sum(values) / len(values)
            print(f'{metric_name}: {avg_score}')

    print()
