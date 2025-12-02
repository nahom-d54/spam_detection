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

## Download from Google Drive

If you have your models in Google Drive:

```python
# In Google Colab
from google.colab import files

# Download model
files.download('/content/gdrive/MyDrive/enron_spam_data_extracted/spam_classifier_model.joblib')

# Download vectorizer  
files.download('/content/gdrive/MyDrive/enron_spam_data_extracted/tfidf_vectorizer.joblib')
```

Then place the downloaded files in this directory.
