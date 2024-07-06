import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

# Load the dataset
dataset_path = r'C:\Users\ASUS\PycharmProjects\FinalYearProject\recommender\item_dataset.xlsx'
df = pd.read_excel(dataset_path)

interactions = df.shape[0]  # Number of interactions
companies = df['job_company'].nunique()  # Number of unique companies
users = interactions # Number of users

# Print the metrics
print(f"Number of interactions: {interactions}")
print(f"Number of unique companies: {companies}")
print(f"Number of unique users: {users}")
print(f"Average number of interactions per user: {round(interactions / users, 2)}")
print(f"Average number of interactions per company: {round(interactions / companies, 2)}")

# Plotting using Seaborn
sns.countplot(x='job_rating', data=df, palette='pastel')
plt.xlabel('Rating', fontsize=16)
plt.ylabel('Count', fontsize=16)
plt.title('Distribution of Job Ratings', fontsize=16)
plt.show()
