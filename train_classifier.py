"""
Training script for the TF-IDF category classification model.
Run this script to train and save the classification model.
"""

from app.classification_service import ClassificationService


def get_training_data():
    """
    Get training data for the classification model.
    Returns lists of texts and corresponding labels.
    """
    texts = [
        # Common category - General queries, greetings, simple questions
        "Hello",
        "Hi there",
        "Good morning",
        "How are you?",
        "What can you help me with?",
        "Tell me about your company",
        "What services do you offer?",
        "Thank you",
        "Thanks for your help",
        "Goodbye",
        "What are your business hours?",
        "Where are you located?",
        "How can I contact you?",
        "Tell me more",
        "I need some information",
        "Can you help me?",
        "What is metro?",
        "Tell me about metro company",
        "What do you do?",
        "How does this work?",

        # Products category - Product inquiries, pricing, specifications
        "What products do you have?",
        "Show me solar panels",
        "I need a 10kW generator",
        "What's the price of inverters?",
        "Do you have battery systems?",
        "Tell me about your solar products",
        "What generators are available?",
        "I'm looking for electrical equipment",
        "What are the specifications of this inverter?",
        "How much does a solar panel cost?",
        "Show me your product catalog",
        "What's the warranty on your products?",
        "Do you have 5kW solar systems?",
        "I need a backup generator",
        "Tell me about solar panel specifications",
        "What models of inverters do you have?",
        "I'm interested in your products",
        "What's the price range for generators?",
        "Do you have portable solar panels?",
        "Show me battery backup systems",
        "I want to buy a solar panel",
        "What's included in the solar package?",
        "Tell me about product features",
        "Do you have commercial generators?",
        "What capacity inverters do you stock?",

        # Salesman category - Sales inquiries, purchasing, quotes, deals
        "I want to buy a solar system",
        "Can I get a quote for installation?",
        "Who can help me with purchasing?",
        "I need to speak with a sales representative",
        "Can you give me a discount?",
        "What's the best deal you have?",
        "I want to place an order",
        "How do I purchase from you?",
        "Can someone help me choose the right product?",
        "I need a sales agent to contact me",
        "What payment options do you have?",
        "Do you offer financing?",
        "I want to buy a generator today",
        "Can I get a bulk discount?",
        "Who handles commercial sales?",
        "I need a quote for 20 solar panels",
        "Connect me with a salesperson",
        "I'm ready to purchase",
        "What are your payment terms?",
        "Do you have any promotions?",
        "I need assistance with buying",
        "Can you recommend a package?",
        "I want to order equipment",
        "Who can give me a price quote?",
        "I need help choosing a system",

        # Employees category - Staff inquiries, departments, positions
        "Who works in the technical department?",
        "I need to contact an employee",
        "Tell me about your staff",
        "Who is the manager?",
        "I need to speak with someone from accounting",
        "What departments do you have?",
        "Can I get contact info for an employee?",
        "Who handles customer service?",
        "I need to reach the IT department",
        "Tell me about your team structure",
        "Who is in charge of operations?",
        "I need to contact HR",
        "What positions are available?",
        "Who works in the office?",
        "I need an employee's contact information",
        "Tell me about your staff members",
        "Who handles logistics?",
        "I need to speak with the administration",
        "What's the organizational structure?",
        "Who is the department head?",
        "I need to contact a specific employee",
        "Tell me about the management team",
        "Who works in procurement?",
        "I need the contact for finance department",
        "Can you connect me with an employee?",

        # Additional mixed examples for better training
        "I have a problem with my solar panel, need repair",  # salesman (technical support)
        "My generator is not working, need a technician",  # salesman
        "What's the price and who can help me buy?",  # salesman
        "Show me products and give me a quote",  # salesman
        "I need employee contact for technical support",  # employees
        "Which staff member handles installations?",  # employees
        "Tell me about solar panels and their prices",  # products
        "Do you have inverters in stock?",  # products
        "What's available for purchase today?",  # salesman
        "I need information about your business",  # common
    ]

    labels = [
        # Common (20)
        "common", "common", "common", "common", "common",
        "common", "common", "common", "common", "common",
        "common", "common", "common", "common", "common",
        "common", "common", "common", "common", "common",

        # Products (25)
        "products", "products", "products", "products", "products",
        "products", "products", "products", "products", "products",
        "products", "products", "products", "products", "products",
        "products", "products", "products", "products", "products",
        "products", "products", "products", "products", "products",

        # Salesman (25)
        "salesman", "salesman", "salesman", "salesman", "salesman",
        "salesman", "salesman", "salesman", "salesman", "salesman",
        "salesman", "salesman", "salesman", "salesman", "salesman",
        "salesman", "salesman", "salesman", "salesman", "salesman",
        "salesman", "salesman", "salesman", "salesman", "salesman",

        # Employees (25)
        "employees", "employees", "employees", "employees", "employees",
        "employees", "employees", "employees", "employees", "employees",
        "employees", "employees", "employees", "employees", "employees",
        "employees", "employees", "employees", "employees", "employees",
        "employees", "employees", "employees", "employees", "employees",

        # Mixed examples (10)
        "salesman", "salesman", "salesman", "salesman", "employees",
        "employees", "products", "products", "salesman", "common",
    ]

    return texts, labels


def main():
    """Train and save the classification model"""
    print("=" * 60)
    print("Training TF-IDF Category Classification Model")
    print("=" * 60)

    # Get training data
    print("\n1. Loading training data...")
    texts, labels = get_training_data()
    print(f"   ✓ Loaded {len(texts)} training examples")

    # Count examples per category
    from collections import Counter
    label_counts = Counter(labels)
    print("\n2. Training data distribution:")
    for label, count in sorted(label_counts.items()):
        print(f"   - {label}: {count} examples")

    # Initialize classification service
    print("\n3. Initializing classification service...")
    classifier = ClassificationService()

    # Train the model
    print("\n4. Training TF-IDF + Logistic Regression pipeline...")
    classifier.train(texts, labels)

    # Test the model
    print("\n5. Testing the trained model...")
    test_queries = [
        "I want to buy a solar panel",
        "Who is the manager?",
        "What products do you have?",
        "Hello, how can you help me?",
        "I need a quote for a generator",
    ]

    print("\nTest Results:")
    print("-" * 60)
    for query in test_queries:
        category, confidence = classifier.classify(query)
        print(f"\nQuery: {query}")
        print(f"Predicted Category: {category}")
        print(f"Confidence Scores:")
        for cat, score in sorted(confidence.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {cat}: {score:.3f}")

    print("\n" + "=" * 60)
    print("✓ Training completed successfully!")
    print("Model saved to: models/category_model.pkl")
    print("=" * 60)


if __name__ == "__main__":
    main()
