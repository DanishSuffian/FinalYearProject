import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from nltk.corpus import stopwords
import string

# Initialize spaCy and NLTK stopwords
nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words('english'))
punctuation = set(string.punctuation)


# Preprocess function for processing 'combined_text'
def preprocess_text(text):
    doc = nlp(text)
    processed_text = []

    for token in doc:
        if token.pos_ != "STOP" and token.text.lower() not in stop_words and token.text.lower() not in punctuation:
            processed_text.append(token.text.lower())

    processed_text = " ".join(processed_text)
    return processed_text


# Load the dataset into a pandas DataFrame
df = pd.read_csv('sentiment_item_dataset.csv')

# Combine relevant text columns such as 'job_company', 'job_location', 'job_type' and 'job_scope'
# into a single text column for each item named 'combined_text'
df['combined_text'] = df['job_company'] + ' ' + df['job_location'] + ' ' + df[
    'job_type'] + ' ' + df['job_scope']

# Replace null values with empty strings
df['combined_text'] = df['combined_text'].fillna('')

# Apply preprocessing to 'combined_text' column
df['combined_text'] = df['combined_text'].apply(preprocess_text)

# Group by company before calculating the similarity score
grouped_df = df.groupby('job_company')['combined_text'].apply(lambda x: ' '.join(x)).reset_index()

# Initialize TF-IDF vectorizer and fit-transform the text within each group
tfidf_vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf_vectorizer.fit_transform(grouped_df['combined_text'])

# Initialize Truncated SVD for dimensionality reduction within each group
n_components = 100
svd = TruncatedSVD(n_components=n_components)
tfidf_matrix_svd = svd.fit_transform(tfidf_matrix)

# Compute cosine similarity matrix within each group
cosine_sim_matrix = cosine_similarity(tfidf_matrix_svd, tfidf_matrix_svd)

# Append the similarity score to the grouped DataFrame
grouped_df['similarity_score'] = cosine_sim_matrix.tolist()

# Save the DataFrame to a new CSV file with the similarity score
grouped_df.to_csv('item_similarity_score.csv', index=False)
