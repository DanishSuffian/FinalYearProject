import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from textblob import TextBlob
from flair.models import TextClassifier
from flair.data import Sentence


# Apply sentiment analysis using TextBlob
def textblob_sentiment_analysis(text):
    if isinstance(text, str):  # Check if text is a string
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        if polarity > 0.5:
            return 2  # Very Positive
        elif 0.25 < polarity <= 0.5:
            return 1  # Positive
        elif -0.25 <= polarity <= 0.25:
            return 0  # Neutral
        elif -0.5 <= polarity < -0.25:
            return -1  # Negative
        else:
            return -2  # Very Negative
    else:
        return 0  # Return neutral sentiment for missing values


# Apply sentiment analysis using VADER
def vader_sentiment_analysis(text):
    if isinstance(text, str):  # Check if text is a string
        sid = SentimentIntensityAnalyzer()
        scores = sid.polarity_scores(text)
        compound_score = scores['compound']
        if compound_score >= 0.5:
            return 2  # Very Positive
        elif 0.1 < compound_score < 0.5:
            return 1  # Positive
        elif -0.1 <= compound_score <= 0.1:
            return 0  # Neutral
        elif -0.5 < compound_score < -0.1:
            return -1  # Negative
        else:
            return -2  # Very Negative
    else:
        return 0  # Return neutral sentiment for missing values


# Apply sentiment analysis using Flair
def flair_sentiment_analysis(text):
    if isinstance(text, str):  # Check if text is a string
        sentence = Sentence(text)
        classifier = TextClassifier.load('en-sentiment')
        classifier.predict(sentence)
        label = sentence.labels[0]
        if label.value == 'POSITIVE':
            return 2  # Very Positive
        elif label.value == 'NEGATIVE':
            return -2  # Very Negative
        elif label.value == 'NEUTRAL':
            return 0  # Neutral
    else:
        return 0  # Return neutral sentiment for missing values


# Load the dataset into a pandas DataFrame
df = pd.read_csv("item_processed_dataset.csv")

# Apply sentiment analysis
df['textblob_sentiment'] = df['review_text'].apply(textblob_sentiment_analysis)
df['vader_sentiment'] = df['review_text'].apply(vader_sentiment_analysis)
df['flair_sentiment'] = df['review_text'].apply(flair_sentiment_analysis)

# Calculate average sentiment score from the three libraries
df['average_sentiment'] = df[['vader_sentiment', 'textblob_sentiment', 'flair_sentiment']].mean(axis=1)

# Group by company and calculate average sentiment score for each company
average_sentiment_by_company = df.groupby('job_company')['average_sentiment'].mean()

# Join the average sentiment by company with the original DataFrame
df = df.merge(average_sentiment_by_company, on='job_company', how='left', suffixes=('', '_avg_company'))

# Save the DataFrame to a CSV file
df.to_csv("item_sentiment_dataset.csv", index=False)
