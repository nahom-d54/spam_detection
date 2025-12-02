"""Spam classification service using pre-trained ML model."""
import joblib
import re
import os
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from typing import Optional
from app.core.config import get_settings

settings = get_settings()


class SpamClassifier:
    """Spam email classifier using pre-trained TF-IDF + ML model."""
    
    def __init__(self):
        """Initialize the spam classifier and download required NLTK data."""
        self.model = None
        self.vectorizer = None
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = None
        self._download_nltk_data()
        self._load_models()
    
    def _download_nltk_data(self):
        """Download necessary NLTK data if not already present."""
        nltk_data = ['stopwords', 'wordnet', 'omw-1.4', 'punkt', 'punkt_tab']
        
        for data in nltk_data:
            try:
                nltk.data.find(f'corpora/{data}' if data in ['stopwords', 'wordnet', 'omw-1.4'] else f'tokenizers/{data}')
            except LookupError:
                print(f"Downloading NLTK data: {data}")
                nltk.download(data, quiet=True)
        
        self.stop_words = set(stopwords.words('english'))
    
    def _load_models(self):
        """Load the pre-trained model and vectorizer."""
        model_path = settings.SPAM_MODEL_PATH
        vectorizer_path = settings.VECTORIZER_PATH
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                "Please place spam_classifier_model.joblib in the models/ directory."
            )
        
        if not os.path.exists(vectorizer_path):
            raise FileNotFoundError(
                f"Vectorizer file not found at {vectorizer_path}. "
                "Please place tfidf_vectorizer.joblib in the models/ directory."
            )
        
        try:
            self.vectorizer = joblib.load(vectorizer_path)
            self.model = joblib.load(model_path)
            print("✓ Spam classifier model and vectorizer loaded successfully!")
        except Exception as e:
            raise RuntimeError(f"Error loading model files: {e}")
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess email text for classification.
        
        Steps:
        1. Convert to lowercase
        2. Remove numbers
        3. Remove punctuation
        4. Tokenize
        5. Remove stop words
        6. Lemmatize tokens
        
        Args:
            text: Raw email text
            
        Returns:
            Preprocessed text string
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove numbers
        text = re.sub(r'\d+', '', text)
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stop words and lemmatize
        cleaned_tokens = []
        for token in tokens:
            if token not in self.stop_words:
                cleaned_tokens.append(self.lemmatizer.lemmatize(token))
        
        # Join back into string
        return ' '.join(cleaned_tokens)
    
    def predict(self, email_text: str) -> bool:
        """
        Predict if an email is spam.
        
        Args:
            email_text: The email content (subject + body)
            
        Returns:
            True if spam, False if ham (legitimate email)
        """
        if not self.model or not self.vectorizer:
            raise RuntimeError("Model not loaded. Cannot make predictions.")
        
        # Preprocess the text
        processed_text = self.preprocess_text(email_text)
        
        # Transform using TF-IDF vectorizer
        text_features = self.vectorizer.transform([processed_text])
        
        # Make prediction
        prediction = self.model.predict(text_features)
        
        # Return True if spam (1), False if ham (0)
        return bool(prediction[0] == 1)
    
    def predict_with_confidence(self, email_text: str) -> tuple[bool, float]:
        """
        Predict if an email is spam with confidence score.
        
        Args:
            email_text: The email content (subject + body)
            
        Returns:
            Tuple of (is_spam, confidence_score)
        """
        if not self.model or not self.vectorizer:
            raise RuntimeError("Model not loaded. Cannot make predictions.")
        
        # Preprocess the text
        processed_text = self.preprocess_text(email_text)
        
        # Transform using TF-IDF vectorizer
        text_features = self.vectorizer.transform([processed_text])
        
        # Make prediction
        prediction = self.model.predict(text_features)
        
        # Get probability if available
        try:
            probabilities = self.model.predict_proba(text_features)
            confidence = float(max(probabilities[0]))
        except AttributeError:
            # Model doesn't support predict_proba
            confidence = 1.0
        
        is_spam = bool(prediction[0] == 1)
        
        return is_spam, confidence


# Global classifier instance (singleton pattern)
_classifier_instance: Optional[SpamClassifier] = None


def get_spam_classifier() -> SpamClassifier:
    """Get the global spam classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SpamClassifier()
    return _classifier_instance
