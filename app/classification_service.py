"""
Classification Service for categorizing user questions using TF-IDF.
Loads the trained model and classifies queries into: common, employees, products, salesman
"""

import pickle
import os
from typing import Dict, List, Tuple

# Optional sklearn import - will use fallback classification if not available
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not installed. Using fallback keyword-based classification.")


class ClassificationService:
    def __init__(self, model_path: str = "models/category_model.pkl"):
        """
        Initialize the classification service.

        Args:
            model_path: Path to the trained classification model
        """
        self.model_path = model_path
        self.pipeline = None
        self.categories = ['common', 'employees', 'products', 'salesman']

        # Load the model if it exists
        if os.path.exists(model_path):
            self.load_model()
        else:
            print(f"Warning: Model file not found at {model_path}")
            print("Please train the model using train_classifier.py")

    def load_model(self):
        """Load the trained TF-IDF classification model"""
        try:
            with open(self.model_path, 'rb') as f:
                self.pipeline = pickle.load(f)
            print(f"✓ Classification model loaded from {self.model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.pipeline = None

    def save_model(self):
        """Save the trained model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.pipeline, f)
            print(f"✓ Model saved to {self.model_path}")
        except Exception as e:
            print(f"Error saving model: {e}")

    def train(self, texts: List[str], labels: List[str]):
        """
        Train the TF-IDF classification pipeline.

        Args:
            texts: List of training text samples
            labels: List of corresponding category labels
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for training. Please install it: pip install scikit-learn")

        # Create pipeline
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                stop_words='english'
            )),
            ('clf', LogisticRegression(
                max_iter=1000,
                random_state=42,
                multi_class='multinomial'
            ))
        ])

        # Train the model
        self.pipeline.fit(texts, labels)
        print("✓ Model training completed")

        # Save the model
        self.save_model()

    def classify(self, text: str) -> Tuple[str, Dict[str, float]]:
        """
        Classify a user query into one of the categories.

        Args:
            text: User query text

        Returns:
            Tuple of (predicted_category, confidence_scores_dict)
        """
        if self.pipeline is None:
            # Fallback to simple keyword-based classification
            return self._fallback_classify(text)

        try:
            # Get prediction
            prediction = self.pipeline.predict([text])[0]

            # Get confidence scores for all categories
            probabilities = self.pipeline.predict_proba([text])[0]
            confidence_scores = {
                category: float(prob)
                for category, prob in zip(self.categories, probabilities)
            }

            return prediction, confidence_scores
        except Exception as e:
            print(f"Error during classification: {e}")
            return self._fallback_classify(text)

    def _fallback_classify(self, text: str) -> Tuple[str, Dict[str, float]]:
        """
        Fallback keyword-based classification when model is not available.

        Args:
            text: User query text

        Returns:
            Tuple of (predicted_category, confidence_scores_dict)
        """
        text_lower = text.lower()

        # Keywords for each category
        products_keywords = ['buy', 'purchase', 'price', 'cost', 'product', 'solar',
                            'generator', 'inverter', 'panel', 'battery', 'equipment',
                            'specification', 'specs', 'model', 'warranty']

        salesman_keywords = ['sales', 'salesman', 'representative', 'agent',
                            'quote', 'deal', 'discount', 'order', 'representative']

        employees_keywords = ['employee', 'staff', 'department', 'position',
                             'manager', 'contact', 'office', 'team']

        technician_keywords = ['technician', 'repair', 'fix', 'problem', 'issue',
                              'fault', 'broken', 'not working', 'maintenance',
                              'install', 'installation', 'service']

        # Count keyword matches
        products_score = sum(1 for kw in products_keywords if kw in text_lower)
        salesman_score = sum(1 for kw in salesman_keywords if kw in text_lower)
        employees_score = sum(1 for kw in employees_keywords if kw in text_lower)

        # Note: technician queries often involve products, so we check for both
        if any(kw in text_lower for kw in technician_keywords):
            salesman_score += 2  # Boost salesman for technical support

        # Determine category
        scores = {
            'products': products_score,
            'salesman': salesman_score,
            'employees': employees_score
        }

        max_score = max(scores.values())

        if max_score == 0:
            # Default to common for general queries
            return 'common', {'common': 0.7, 'employees': 0.1, 'products': 0.1, 'salesman': 0.1}

        # Normalize scores to probabilities
        total = sum(scores.values()) + 0.1  # Add small constant to avoid division by zero
        confidence_scores = {
            category: score / total
            for category, score in scores.items()
        }
        confidence_scores['common'] = 0.1 / total

        predicted = max(scores.items(), key=lambda x: x[1])[0]

        return predicted, confidence_scores

    def get_category_info(self, category: str) -> Dict[str, any]:
        """
        Get information about what data should be fetched for each category.

        Args:
            category: The predicted category

        Returns:
            Dictionary with category metadata
        """
        category_config = {
            'common': {
                'fetch_data': False,
                'data_sources': [],
                'response_style': 'short',
                'max_recommendations': 0,
                'description': 'General queries, greetings, or simple questions'
            },
            'products': {
                'fetch_data': True,
                'data_sources': ['search_products'],
                'response_style': 'detailed',
                'max_recommendations': 2,
                'description': 'Product-related queries, pricing, specifications'
            },
            'salesman': {
                'fetch_data': True,
                'data_sources': ['search_salesmen', 'search_products'],
                'response_style': 'detailed',
                'max_recommendations': 2,
                'description': 'Sales inquiries, purchasing assistance, quotes'
            },
            'employees': {
                'fetch_data': True,
                'data_sources': ['search_employees'],
                'response_style': 'detailed',
                'max_recommendations': 2,
                'description': 'Employee information, departments, staff contacts'
            }
        }

        return category_config.get(category, category_config['common'])

    def should_fetch_data(self, category: str) -> bool:
        """Check if data should be fetched for this category"""
        return self.get_category_info(category)['fetch_data']

    def get_data_sources(self, category: str) -> List[str]:
        """Get list of data sources to query for this category"""
        return self.get_category_info(category)['data_sources']

    def get_response_style(self, category: str) -> str:
        """Get the response style (short/detailed) for this category"""
        return self.get_category_info(category)['response_style']

    def get_max_recommendations(self, category: str) -> int:
        """Get maximum number of recommendations for this category"""
        return self.get_category_info(category)['max_recommendations']
