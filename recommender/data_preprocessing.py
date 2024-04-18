import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Create a set of English stopwords using NLTK's 'stopwords' corpus
stop_words = set(stopwords.words('english'))
# Initialize WordNet lemmatizer object
lemmatizer = WordNetLemmatizer()


# Preprocess function for replacing value containing K with 1000
def preprocess_value(value):
    # Check if the data contains 'K' in it such as '1.9K', if so, replace with 1000
    if isinstance(value, str) and 'K' in value:
        return float(value.replace('K', '')) * 1000
    else:
        return value


# Preprocess function for processing 'review_text'
def preprocess_text(text):
    # Check if the text is null, if so, return an empty string
    if pd.isna(text):
        return ''

    # Tokenization of the text
    tokens = word_tokenize(text)
    # Lower-casing words and removing punctuation
    tokens = [word.lower() for word in tokens if word.isalpha()]
    # Removing stopwords
    tokens = [word for word in tokens if word not in stop_words]
    # Lemmatization
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return ' '.join(tokens)


# Load the dataset into a pandas DataFrame
df = pd.read_excel("item_dataset.xlsx")

# Apply the preprocess_value function to the 'job_interview' and 'job_salaries' columns
df['job_interview'] = df['job_interview'].apply(preprocess_value)
df['job_salaries'] = df['job_salaries'].apply(preprocess_value)

# Drop unused columns
columns_to_drop = ['sub_job_company', 'sub_job_company-href', 'pagination', 'job_reviews']
df.drop(columns=columns_to_drop, inplace=True)

# Filter based on companies that is located in Malaysia according to column 'job_location'
df = df[df['job_location'].str.contains('Malaysia', na=False)]

# Aggregate reviews per company and assign values to 'review_count'
reviews_group_by_company = df.groupby('job_company').size().reset_index(name='review_count')

# Filter based on companies with more than 10 reviews according to the values in 'review_count'
company_more_than_10_reviews = reviews_group_by_company[reviews_group_by_company['review_count'] > 10]

# Merge filtered companies back with the original dataset 'df'
df_filtered = pd.merge(df, company_more_than_10_reviews, on='job_company', how='inner')

# Remove '-' from 'job_pros' and 'job_cons' columns
df_filtered['job_pros'] = df_filtered['job_pros'].str.lstrip('-')
df_filtered['job_cons'] = df_filtered['job_cons'].str.lstrip('-')

# Concatenate 'job_pros' and 'job_cons' columns into a single column called 'review_text'
df_filtered['review_text'] = df_filtered['job_pros'] + " " + df_filtered['job_cons']

# Apply preprocessing to 'review_text' column
df_filtered['preprocessed_review_text'] = df_filtered['review_text'].apply(preprocess_text)

# Save the processed DataFrame to a CSV file
df_filtered.to_csv("item_processed_dataset.csv", index=False)
