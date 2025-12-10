# TF-IDF Classification Pipeline

This document describes the TF-IDF-based classification system that categorizes user questions and provides context-aware responses.

## Overview

The classification pipeline uses TF-IDF (Term Frequency-Inverse Document Frequency) with Logistic Regression to classify user queries into four categories:

1. **common** - General queries, greetings, simple questions
2. **products** - Product inquiries, specifications, pricing
3. **salesman** - Purchase inquiries, quotes, technical support
4. **employees** - Staff inquiries, department information

## Pipeline Components

### TfidfVectorizer
Converts text into numerical features using:
- Max features: 1000
- N-gram range: (1, 2) - unigrams and bigrams
- Stop words: English

### LogisticRegression Classifier
Multi-class classifier with:
- Max iterations: 1000
- Multi-class: Multinomial
- Random state: 42 (for reproducibility)

## How It Works

### 1. Classification Flow

```
User Query
    ↓
ClassificationService.classify()
    ↓
TF-IDF Model (or fallback keyword-based)
    ↓
Category + Confidence Scores
    ↓
ChatbotService.generate_llm_response()
    ↓
Category-aware LLM prompt
    ↓
Response + Filtered Recommendations
```

### 2. Category-Based Response Adjustment

#### Common Category
- **Response Style**: SHORT (1 sentence max)
- **Fetch Data**: No
- **Recommendations**: 0
- **Use Case**: Greetings, simple questions, casual conversation

#### Products Category
- **Response Style**: DETAILED (2-3 sentences)
- **Fetch Data**: Yes (search_products)
- **Recommendations**: Up to 2 products
- **Use Case**: Product queries, specifications, pricing

#### Salesman Category
- **Response Style**: DETAILED (2-3 sentences)
- **Fetch Data**: Yes (search_salesmen, search_products)
- **Recommendations**: Up to 2 salesmen and products
- **Use Case**: Purchase inquiries, quotes, technical support needs

#### Employees Category
- **Response Style**: DETAILED (2-3 sentences)
- **Fetch Data**: Yes (search_employees)
- **Recommendations**: Up to 2 employees
- **Use Case**: Staff contact, department information

## Installation & Setup

### 1. Install Dependencies

```bash
pip install scikit-learn
```

Or using the requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Train the Model

```bash
python train_classifier.py
```

This will:
- Load training data (105 samples across 4 categories)
- Train TF-IDF + Logistic Regression pipeline
- Save model to `models/category_model.pkl`
- Show test results with sample queries

### 3. Test the Classification

```bash
python test_classification.py
```

Expected output:
- Classification accuracy (target: >80%)
- Confidence scores for each query
- Category configuration details

## Usage in Code

### Basic Classification

```python
from app.classification_service import ClassificationService

# Initialize classifier
classifier = ClassificationService()

# Classify a query
category, confidence = classifier.classify("I want to buy a solar panel")

print(f"Category: {category}")
print(f"Confidence: {confidence[category]:.2f}")
```

### Integration with Chatbot

The classification is automatically integrated in `ChatbotService.generate_llm_response()`:

1. User message is classified
2. Category determines:
   - Response length/detail level
   - Which data sources to query
   - Maximum number of recommendations
3. LLM receives category-aware system prompt
4. Response is generated with appropriate style

## Fallback Classification

If scikit-learn is not installed, the system uses keyword-based classification:

- **Products**: Matches keywords like "buy", "price", "solar", "generator"
- **Salesman**: Matches "quote", "sales", "purchase", "repair", "problem"
- **Employees**: Matches "employee", "staff", "department", "manager"
- **Common**: Default for queries with no strong keyword matches

Fallback accuracy: ~84% (as tested)

## Model Training Data

The model is trained on 105 examples:
- 20 common examples
- 25 products examples
- 25 salesman examples
- 25 employees examples
- 10 mixed examples

To improve accuracy, add more training examples to `train_classifier.py`.

## File Structure

```
metro_CHATBOT/
├── app/
│   ├── classification_service.py   # Main classification service
│   ├── chatbot_service.py          # Integrated with classifier
│   └── llm_service.py               # Category-aware prompts
├── models/
│   └── category_model.pkl          # Trained TF-IDF model
├── train_classifier.py             # Training script
├── test_classification.py          # Testing script
└── CLASSIFICATION_PIPELINE.md      # This document
```

## API Response Format

The chatbot API returns recommendations filtered by category:

```json
{
  "bot_message": "Response text (length based on category)",
  "recommends": {
    "products": [],      // Up to 2 for products/salesman categories
    "technicians": [],   // Up to 2 for salesman category
    "salesman": [],      // Up to 2 for salesman category
    "employees": [],     // Up to 2 for employees category
    "extra_info": "Category: products"
  },
  "next_step": ["Ask another question", "View more products", ...]
}
```

For **common** category, all recommendation lists are empty.

## Performance Metrics

### Fallback Classifier (Keyword-based)
- **Accuracy**: 84.2% (16/19 test queries)
- **Common**: 100% (4/4)
- **Products**: 100% (5/5)
- **Salesman**: 60% (3/5)
- **Employees**: 80% (4/5)

### TF-IDF Classifier (Expected with trained model)
- **Target Accuracy**: >90%
- **Requires**: scikit-learn installation and model training

## Customization

### Adding New Categories

1. Update `categories` list in `ClassificationService`
2. Add training examples in `train_classifier.py`
3. Add category configuration in `get_category_info()`
4. Update LLM prompts in `llm_service.py`
5. Retrain the model

### Adjusting Response Styles

Edit the `category_instructions` in `llm_service.py`:

```python
category_instructions = {
    "common": """Your custom instructions...""",
    # ... other categories
}
```

### Tuning Recommendations

Modify `max_recommendations` in `ClassificationService.get_category_info()`:

```python
'products': {
    'max_recommendations': 3,  # Show up to 3 products
    # ...
}
```

## Troubleshooting

### Issue: "Module 'sklearn' not found"
**Solution**: Install scikit-learn: `pip install scikit-learn`
**Note**: System will use fallback classification until sklearn is installed

### Issue: "Model file not found"
**Solution**: Train the model: `python train_classifier.py`
**Note**: System will use fallback classification until model is trained

### Issue: Low classification accuracy
**Solution**: Add more diverse training examples to `train_classifier.py` and retrain

### Issue: Wrong category predictions
**Solution**:
1. Check training data for similar examples
2. Add more examples for the confused categories
3. Adjust keyword lists in `_fallback_classify()` for fallback mode

## Future Improvements

1. **Expand Training Data**: Add more diverse examples (500+ samples)
2. **Cross-validation**: Implement k-fold cross-validation
3. **Feature Engineering**: Add custom features (question words, product names)
4. **Ensemble Methods**: Combine TF-IDF with other classifiers
5. **Online Learning**: Update model based on user feedback
6. **Confidence Threshold**: Ask for clarification on low-confidence predictions
7. **Multi-label Classification**: Support queries spanning multiple categories

## References

- TF-IDF: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
- Logistic Regression: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
- Pipeline: https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html
