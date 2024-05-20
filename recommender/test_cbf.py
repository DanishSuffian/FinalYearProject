from sklearn.decomposition import TruncatedSVD, NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
import string
import pandas as pd
import spacy

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
df = pd.read_csv('item_sentiment_dataset.csv')

# Combine relevant text columns into a single text column 'combined_text'
df['combined_text'] = df['job_company'] + ' ' + df['job_location'] + ' ' + df['job_type'] + ' ' + df['job_scope']
df['combined_text'] = df['combined_text'].fillna('')

# Apply preprocessing to 'combined_text' column
df['combined_text'] = df['combined_text'].apply(preprocess_text)

# Group by company before calculating the similarity score
grouped_df = df.groupby('job_company')['combined_text'].apply(lambda x: ' '.join(x)).reset_index()

# Initialize TF-IDF vectorizer and fit-transform the text within each group
tfidf_vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf_vectorizer.fit_transform(grouped_df['combined_text'])

# Initialize Truncated SVD, NMF, and LSA models
n_components = 100
svd = TruncatedSVD(n_components=n_components)
nmf = NMF(n_components=n_components)
lsa = TruncatedSVD(n_components=n_components)  # LSA using TruncatedSVD

# Fit-transform TF-IDF matrix using Truncated SVD, NMF, and LSA
tfidf_matrix_svd = svd.fit_transform(tfidf_matrix)
tfidf_matrix_nmf = nmf.fit_transform(tfidf_matrix)
tfidf_matrix_lsa = lsa.fit_transform(tfidf_matrix)

# Compute cosine similarity matrix for Truncated SVD, NMF, and LSA
cosine_sim_matrix_svd = cosine_similarity(tfidf_matrix_svd, tfidf_matrix_svd)
cosine_sim_matrix_nmf = cosine_similarity(tfidf_matrix_nmf, tfidf_matrix_nmf)
cosine_sim_matrix_lsa = cosine_similarity(tfidf_matrix_lsa, tfidf_matrix_lsa)

# Append the similarity scores to the grouped DataFrame
grouped_df['similarity_score_svd'] = cosine_sim_matrix_svd.tolist()
grouped_df['similarity_score_nmf'] = cosine_sim_matrix_nmf.tolist()
grouped_df['similarity_score_lsa'] = cosine_sim_matrix_lsa.tolist()

# Evaluate Truncated SVD
avg_similarity_scores_svd = grouped_df['similarity_score_svd'].apply(lambda x: sum(x) / len(x))
diversity_score_svd = avg_similarity_scores_svd.std()
coverage_score_svd = (avg_similarity_scores_svd > 0).sum() / len(avg_similarity_scores_svd) * 100
print("Evaluation Metrics for Truncated SVD:")
print(f'Mean Average Similarity: {avg_similarity_scores_svd.mean()}')
print(f'Diversity Score: {diversity_score_svd}')
print(f'Coverage Score: {coverage_score_svd}%')

# Evaluate NMF
avg_similarity_scores_nmf = grouped_df['similarity_score_nmf'].apply(lambda x: sum(x) / len(x))
diversity_score_nmf = avg_similarity_scores_nmf.std()
coverage_score_nmf = (avg_similarity_scores_nmf > 0).sum() / len(avg_similarity_scores_nmf) * 100
print("\nEvaluation Metrics for NMF:")
print(f'Mean Average Similarity: {avg_similarity_scores_nmf.mean()}')
print(f'Diversity Score: {diversity_score_nmf}')
print(f'Coverage Score: {coverage_score_nmf}%')

# Evaluate LSA
avg_similarity_scores_lsa = grouped_df['similarity_score_lsa'].apply(lambda x: sum(x) / len(x))
diversity_score_lsa = avg_similarity_scores_lsa.std()
coverage_score_lsa = (avg_similarity_scores_lsa > 0).sum() / len(avg_similarity_scores_lsa) * 100
print("\nEvaluation Metrics for LSA:")
print(f'Mean Average Similarity: {avg_similarity_scores_lsa.mean()}')
print(f'Diversity Score: {diversity_score_lsa}')
print(f'Coverage Score: {coverage_score_lsa}%')
