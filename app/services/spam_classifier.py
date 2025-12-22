"""Spam classification service using pre-trained ML model."""

import os
import re
from typing import Optional

import joblib
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

from app.core.config import get_settings

settings = get_settings()


class SpamClassifier:
    """Spam email classifier using pre-trained TF-IDF + ML model."""

    def __init__(self, model_type: Optional[str] = None):
        """Initialize the spam classifier and download required NLTK data.

        Args:
            model_type: Type of model to use ('nb' for Naive Bayes, 'lr' for Logistic Regression).
                       If None, uses the value from settings.
        """
        self.pipeline = None
        self.model_type = model_type or settings.SPAM_MODEL_TYPE
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = None
        self._download_nltk_data()
        self._load_pipeline()

    def _download_nltk_data(self):
        """Download necessary NLTK data if not already present."""
        nltk_data = ["stopwords", "wordnet", "omw-1.4", "punkt", "punkt_tab"]

        for data in nltk_data:
            try:
                nltk.data.find(
                    f"corpora/{data}"
                    if data in ["stopwords", "wordnet", "omw-1.4"]
                    else f"tokenizers/{data}"
                )
            except LookupError:
                print(f"Downloading NLTK data: {data}")
                nltk.download(data, quiet=True)

        self.stop_words = set(stopwords.words("english"))

    def _load_pipeline(self):
        """Load the pre-trained pipeline (TF-IDF + Classifier)."""
        # Determine model path based on model type
        model_filename = f"model_{self.model_type}.joblib"
        model_path = os.path.join("models", model_filename)

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at {model_path}. "
                f"Please place {model_filename} in the models/ directory. "
                f"Available model types: 'nb' (Naive Bayes) or 'lr' (Logistic Regression)"
            )

        try:
            self.pipeline = joblib.load(model_path)
            model_name = (
                "Naive Bayes" if self.model_type == "nb" else "Logistic Regression"
            )
            print(f"✓ Spam classifier pipeline ({model_name}) loaded successfully!")
        except Exception as e:
            raise RuntimeError(f"Error loading pipeline file: {e}")

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
        text = re.sub(r"\d+", "", text)

        # Remove punctuation
        text = re.sub(r"[^\w\s]", "", text)

        # Tokenize
        tokens = word_tokenize(text)

        # Remove stop words and lemmatize
        cleaned_tokens = []
        for token in tokens:
            if token not in self.stop_words:
                cleaned_tokens.append(self.lemmatizer.lemmatize(token))

        # Join back into string
        return " ".join(cleaned_tokens)

    def predict(self, email_text: str) -> bool:
        """
        Predict if an email is spam.

        Args:
            email_text: The email content (subject + body)

        Returns:
            True if spam, False if ham (legitimate email)
        """
        if not self.pipeline:
            raise RuntimeError("Pipeline not loaded. Cannot make predictions.")

        # Preprocess the text
        processed_text = self.preprocess_text(email_text)

        # Pipeline handles TF-IDF transformation and prediction
        prediction = self.pipeline.predict([processed_text])

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
        if not self.pipeline:
            raise RuntimeError("Pipeline not loaded. Cannot make predictions.")

        # Preprocess the text
        processed_text = self.preprocess_text(email_text)

        # Pipeline handles TF-IDF transformation and prediction
        prediction = self.pipeline.predict([processed_text])

        # Get probability if available
        try:
            probabilities = self.pipeline.predict_proba([processed_text])
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
