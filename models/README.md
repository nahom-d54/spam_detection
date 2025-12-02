# ML Models Directory

Place your pre-trained spam classification models here:

## Required Files

1. **spam_classifier_model.joblib** - Trained spam classifier model
2. **tfidf_vectorizer.joblib** - TF-IDF vectorizer

## Model Training

Your models were trained using:

- Dataset: Enron spam dataset
- Preprocessing: Lowercase, remove numbers/punctuation, tokenization, stop word removal, lemmatization
- Vectorization: TF-IDF
- Algorithm: (Based on your training)

## Usage

The models are automatically loaded by `app/services/spam_classifier.py` when the FastAPI application starts.
