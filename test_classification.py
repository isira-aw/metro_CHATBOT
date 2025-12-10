"""
Test script for the TF-IDF classification pipeline
"""

from app.classification_service import ClassificationService


def test_classification():
    """Test the classification service with various queries"""

    print("=" * 70)
    print("Testing TF-IDF Classification Pipeline")
    print("=" * 70)

    # Initialize the classifier (will use fallback if model not trained)
    classifier = ClassificationService()

    # Test queries
    test_queries = [
        # Common category
        ("Hello", "common"),
        ("Hi there", "common"),
        ("What can you help me with?", "common"),
        ("Tell me about your company", "common"),

        # Products category
        ("What products do you have?", "products"),
        ("Show me solar panels", "products"),
        ("I need a 10kW generator", "products"),
        ("What's the price of inverters?", "products"),
        ("Tell me about solar panel specifications", "products"),

        # Salesman category
        ("I want to buy a solar system", "salesman"),
        ("Can I get a quote?", "salesman"),
        ("I need to speak with a sales representative", "salesman"),
        ("I have a problem with my generator", "salesman"),
        ("My solar panel is not working", "salesman"),

        # Employees category
        ("Who works in the technical department?", "employees"),
        ("I need to contact an employee", "employees"),
        ("Tell me about your staff", "employees"),
        ("Who is the manager?", "employees"),
        ("I need someone from accounting", "employees"),
    ]

    print("\n" + "=" * 70)
    print("Test Results:")
    print("=" * 70)

    correct = 0
    total = len(test_queries)

    for query, expected_category in test_queries:
        predicted_category, confidence_scores = classifier.classify(query)

        is_correct = predicted_category == expected_category
        if is_correct:
            correct += 1

        status = "✓" if is_correct else "✗"

        print(f"\n{status} Query: \"{query}\"")
        print(f"  Expected: {expected_category}")
        print(f"  Predicted: {predicted_category} (confidence: {confidence_scores.get(predicted_category, 0):.3f})")

        # Show top 3 confidence scores
        top_3 = sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"  Top 3 scores: {', '.join([f'{cat}: {score:.3f}' for cat, score in top_3])}")

    # Show accuracy
    accuracy = (correct / total) * 100
    print("\n" + "=" * 70)
    print(f"Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    print("=" * 70)

    # Test category configuration
    print("\n" + "=" * 70)
    print("Category Configuration:")
    print("=" * 70)

    for category in ['common', 'products', 'salesman', 'employees']:
        config = classifier.get_category_info(category)
        print(f"\n{category.upper()}:")
        print(f"  Response Style: {config['response_style']}")
        print(f"  Fetch Data: {config['fetch_data']}")
        print(f"  Data Sources: {', '.join(config['data_sources']) if config['data_sources'] else 'None'}")
        print(f"  Max Recommendations: {config['max_recommendations']}")
        print(f"  Description: {config['description']}")

    print("\n" + "=" * 70)
    print("✓ Classification test completed!")
    print("=" * 70)


if __name__ == "__main__":
    test_classification()
