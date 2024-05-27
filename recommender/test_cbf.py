from implicit.als import AlternatingLeastSquares
from sklearn.decomposition import TruncatedSVD, NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
import string
import pandas as pd
import spacy
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
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None


# Preprocess function for processing text
def preprocess_text(text):
    doc = nlp(text)
    processed_text = []

    for token in doc:
        if token.pos_ != "STOP" and token.text.lower() not in stop_words and token.text.lower() not in punctuation:
            processed_text.append(token.text.lower())

    processed_text = " ".join(processed_text)
    return processed_text


# Initialize spaCy and NLTK stopwords
nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words('english'))
punctuation = set(string.punctuation)

# Load the dataset from MySQL database
connection = get_db_connection()
if connection:
    try:
        query = "SELECT company_name, company_location, company_type, company_scope FROM companies"
        df = pd.read_sql(query, connection)
    except mysql.connector.Error as e:
        print(f"Error reading data from MySQL: {e}")
    finally:
        connection.close()

# Combine relevant text columns into a single text column 'combined_text'
df['combined_text'] = df['company_name'] + ' ' + df['company_location'] + ' ' + df['company_type'] + ' ' + df['company_scope']
df['combined_text'] = df['combined_text'].fillna('')

# Apply preprocessing to 'combined_text' column
df['combined_text'] = df['combined_text'].apply(preprocess_text)

# Initialize TF-IDF vectorizer and fit-transform the text
tfidf_vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf_vectorizer.fit_transform(df['combined_text'])

# Initialize Truncated SVD, NMF, and ALS models
n_components = 10
svd = TruncatedSVD(n_components=n_components)
nmf = NMF(n_components=n_components, init='random', random_state=0)
als = AlternatingLeastSquares()

# Fit-transform TF-IDF matrix using Truncated SVD, NMF, and ALS
tfidf_matrix_svd = svd.fit_transform(tfidf_matrix)
tfidf_matrix_nmf = nmf.fit_transform(tfidf_matrix)
tfidf_matrix_als = als.fit(tfidf_matrix.T)

item_factors = als.item_factors

# Compute cosine similarity matrix for Truncated SVD, NMF, and ALS
cosine_sim_matrix_tfidf = cosine_similarity(tfidf_matrix, tfidf_matrix)
cosine_sim_matrix_svd = cosine_similarity(tfidf_matrix_svd, tfidf_matrix_svd)
cosine_sim_matrix_nmf = cosine_similarity(tfidf_matrix_nmf, tfidf_matrix_nmf)
cosine_sim_matrix_als = cosine_similarity(item_factors, item_factors)

# Create a DataFrame to store similarity scores
similarity_scores_df = pd.DataFrame({
    'company': df['company_name'],
    'similarity_score_svd': list(cosine_sim_matrix_svd),
    'similarity_score_nmf': list(cosine_sim_matrix_nmf),
    'similarity_score_als': list(cosine_sim_matrix_als.diagonal())
})

# Evaluate TF-IDF
avg_similarity_scores_tfidf = cosine_sim_matrix_tfidf.mean(axis=1)
diversity_score_tfidf = avg_similarity_scores_tfidf.std()
coverage_score_tfidf = (avg_similarity_scores_tfidf > 0).sum() / len(avg_similarity_scores_tfidf) * 100
print("\nEvaluation Metrics for TF-IDF:")
print(f'Mean Average Similarity: {avg_similarity_scores_tfidf.mean()}')
print(f'Diversity Score: {diversity_score_tfidf}')
print(f'Coverage Score: {coverage_score_tfidf}%')

# Evaluate Truncated SVD
avg_similarity_scores_svd = similarity_scores_df['similarity_score_svd'].apply(lambda x: sum(x) / len(x))
diversity_score_svd = avg_similarity_scores_svd.std()
coverage_score_svd = (avg_similarity_scores_svd > 0).sum() / len(avg_similarity_scores_svd) * 100
print("\nEvaluation Metrics for Truncated SVD:")
print(f'Mean Average Similarity: {avg_similarity_scores_svd.mean()}')
print(f'Diversity Score: {diversity_score_svd}')
print(f'Coverage Score: {coverage_score_svd}%')

# Evaluate NMF
avg_similarity_scores_nmf = similarity_scores_df['similarity_score_nmf'].apply(lambda x: sum(x) / len(x))
diversity_score_nmf = avg_similarity_scores_nmf.std()
coverage_score_nmf = (avg_similarity_scores_nmf > 0).sum() / len(avg_similarity_scores_nmf) * 100
print("\nEvaluation Metrics for NMF:")
print(f'Mean Average Similarity: {avg_similarity_scores_nmf.mean()}')
print(f'Diversity Score: {diversity_score_nmf}')
print(f'Coverage Score: {coverage_score_nmf}%')

# Evaluate ALS
avg_similarity_scores_als = cosine_sim_matrix_als.mean(axis=1)
diversity_score_als = avg_similarity_scores_als.std()
coverage_score_als = (avg_similarity_scores_als > 0).sum() / len(avg_similarity_scores_als) * 100
print("\nEvaluation Metrics for ALS:")
print(f'Mean Average Similarity: {avg_similarity_scores_als.mean()}')
print(f'Diversity Score: {diversity_score_als}')
print(f'Coverage Score: {coverage_score_als}%')
