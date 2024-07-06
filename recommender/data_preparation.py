import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

# Load the dataset into a pandas DataFrame
df = pd.read_excel("item_dataset.xlsx")

# Drop unused columns
columns_to_drop = ['sub_job_company', 'sub_job_company-href', 'pagination', 'job_reviews']
df.drop(columns=columns_to_drop, inplace=True)

# Filter based on companies located in Malaysia according to column 'job_location'
df = df[df['job_location'].str.contains('Malaysia', na=False)]

# Aggregate reviews per company and assign values to 'review_count'
reviews_group_by_company = df.groupby('job_company').size().reset_index(name='review_count')

# Filter based on companies with more than 10 reviews according to the values in 'review_count'
company_more_than_10_reviews = reviews_group_by_company[reviews_group_by_company['review_count'] > 10]

# Merge filtered companies back with the original dataset 'df'
df_filtered = pd.merge(df, company_more_than_10_reviews, on='job_company', how='inner')

interactions = df_filtered.shape[0]  # Number of interactions
companies = df_filtered['job_company'].nunique()  # Number of unique companies
users = interactions # Number of users

# Print the metrics
print(f"Number of interactions: {interactions}")
print(f"Number of unique companies: {companies}")
print(f"Number of unique users: {users}")
print(f"Average number of interactions per user: {round(interactions / users, 2)}")
print(f"Average number of interactions per company: {round(interactions / companies, 2)}")
