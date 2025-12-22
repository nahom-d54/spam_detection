# Spam Classifier Integration Guide

## Overview

The spam classifier has been updated to work with the pipeline-based models trained in the `spam_detection.ipynb` notebook. The new architecture uses scikit-learn pipelines that combine TF-IDF vectorization and classification in a single object.

## Changes Made

### 1. **Pipeline-Based Architecture**

- **Before**: Separate vectorizer (`tfidf_vectorizer.joblib`) and model (`spam_classifier_model.joblib`) files
- **After**: Single pipeline file that includes both TF-IDF and classifier (`model_nb.joblib` or `model_lr.joblib`)

### 2. **Model Selection**

Two model types are now available:

- **`nb`**: Multinomial Naive Bayes (faster, good baseline, ~88-92% F1)
- **`lr`**: Logistic Regression with L1 regularization (more accurate, ~90-96% F1)

### 3. **Configuration Updates**

In [app/core/config.py](../app/core/config.py):

```python
# ML Model Configuration
SPAM_MODEL_TYPE: str = "lr"  # Default to Logistic Regression
```

### 4. **Updated SpamClassifier**

- `__init__(model_type: Optional[str] = None)`: Now accepts model type parameter
- `_load_pipeline()`: Loads complete pipeline instead of separate files
- `predict()` and `predict_with_confidence()`: Use pipeline directly

## Setup Instructions

### Step 1: Train Models (if not already done)

1. Open [models/spam_detection.ipynb](../models/spam_detection.ipynb) in Google Colab or Jupyter
2. Run all cells to train both models
3. The notebook will save:
   - `model_nb.joblib` (Naive Bayes pipeline)
   - `model_lr.joblib` (Logistic Regression pipeline)

### Step 2: Copy Trained Models

**Option A: From Google Drive (after Colab training)**
If you trained in Google Colab, the models are saved to Google Drive. Download them and place in the `models/` directory.

**Option B: Using the Copy Script**

```bash
# Copy from a local directory
python scripts/copy_trained_models.py /path/to/your/trained/models
```

**Option C: Manual Copy**
Simply copy `model_nb.joblib` and `model_lr.joblib` to the `models/` directory.

### Step 3: Verify Installation

```bash
# Verify models are present
python scripts/copy_trained_models.py
```

Expected output:

```
✓ model_nb.joblib exists (1.24 MB)
✓ model_lr.joblib exists (2.15 MB)
```

## Usage

### Basic Usage

```python
from app.services.spam_classifier import get_spam_classifier

# Get the default classifier (uses LR by default)
classifier = get_spam_classifier()

# Predict if email is spam
email_text = "Congratulations! You've won a FREE prize! Click here now!"
is_spam = classifier.predict(email_text)
print(f"Is spam: {is_spam}")  # True

# Get prediction with confidence
is_spam, confidence = classifier.predict_with_confidence(email_text)
print(f"Is spam: {is_spam}, Confidence: {confidence:.2%}")
```

### Switching Models

```python
from app.services.spam_classifier import SpamClassifier

# Use Naive Bayes (faster)
nb_classifier = SpamClassifier(model_type='nb')

# Use Logistic Regression (more accurate)
lr_classifier = SpamClassifier(model_type='lr')
```

### Configuration-Based Selection

Set in `.env` or environment variables:

```bash
SPAM_MODEL_TYPE=lr  # or 'nb'
```

## API Integration

The spam classifier is automatically used by the email monitoring worker:

1. Worker fetches new emails via IMAP
2. Each email is preprocessed and classified using the pipeline
3. Spam emails are moved to the spam folder
4. Ham emails remain in inbox

## Model Performance

Based on 5-fold cross-validation on the Enron spam dataset:

| Model               | Mean F1 Score | Training Time | Inference Speed |
| ------------------- | ------------- | ------------- | --------------- |
| Naive Bayes         | 0.88-0.92     | ~2 seconds    | ~0.5ms/email    |
| Logistic Regression | 0.90-0.96     | ~30 seconds   | ~1ms/email      |

**Recommendation**: Use `lr` (Logistic Regression) for production for best accuracy.

## Technical Details

### Pipeline Structure

Each saved model is a scikit-learn Pipeline:

```python
Pipeline([
    ('tfidf', TfidfVectorizer(
        max_features=10000,
        ngram_range=(1,2),  # Only for LR
        max_df=0.9,
        min_df=5
    )),
    ('classifier', MultinomialNB() or LogisticRegression(
        penalty='l1',
        solver='saga',
        max_iter=1000
    ))
])
```

### Preprocessing Pipeline

Text preprocessing (done before pipeline):

1. Lowercase conversion
2. Number removal
3. Punctuation removal
4. Tokenization (NLTK)
5. Stop word removal
6. Lemmatization

### Mathematical Foundation

**TF-IDF**:
$$\text{TF-IDF}(t,d) = \frac{f_{t,d}}{\sum_{t'} f_{t',d}} \times \log\frac{|D|}{|\{d' : t \in d'\}|}$$

**Logistic Regression**:
$$P(\text{spam}|x) = \frac{1}{1 + e^{-(\mathbf{w}^T\mathbf{x} + b)}}$$

**Naive Bayes**:
$$P(\text{spam}|x) \propto P(\text{spam}) \prod_{i} P(x_i|\text{spam})$$

## Troubleshooting

### Model Not Found Error

```
FileNotFoundError: Model file not found at models/model_lr.joblib
```

**Solution**: Run the training notebook and copy the model files to the `models/` directory.

### Import Error

```
ModuleNotFoundError: No module named 'sklearn'
```

**Solution**: Install dependencies:

```bash
pip install -r requirements.txt
```

### NLTK Data Missing

```
LookupError: Resource punkt not found
```

**Solution**: The classifier automatically downloads NLTK data on first run. If this fails, manually download:

```python
import nltk
nltk.download(['stopwords', 'wordnet', 'omw-1.4', 'punkt', 'punkt_tab'])
```

## File Structure

```
spam_detection/
├── models/
│   ├── model_nb.joblib          # Naive Bayes pipeline
│   ├── model_lr.joblib          # Logistic Regression pipeline
│   ├── spam_detection.ipynb     # Training notebook
│   └── enron_spam_data.csv      # Training dataset
├── app/
│   ├── services/
│   │   └── spam_classifier.py   # Updated classifier
│   └── core/
│       └── config.py            # Configuration
└── scripts/
    └── copy_trained_models.py   # Model copy utility
```

## Next Steps

1. ✅ Train models using the notebook
2. ✅ Copy trained models to `models/` directory
3. ✅ Update configuration if needed
4. ✅ Test the classifier with sample emails
5. ✅ Deploy the API and monitor performance
6. 📊 Collect production data for model retraining
7. 🔄 Periodically retrain with new spam examples

## References

- Notebook: [models/spam_detection.ipynb](../models/spam_detection.ipynb)
- Classifier: [app/services/spam_classifier.py](../app/services/spam_classifier.py)
- Configuration: [app/core/config.py](../app/core/config.py)
- Dataset: Enron Email Dataset (ham/spam labels)
