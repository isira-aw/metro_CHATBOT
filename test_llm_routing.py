"""
Test script for the new LLM-based routing system
This tests the chatbot without keywords, letting the LLM decide what data to fetch
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.chatbot_service import ChatbotService
from app.database import init_db
import json


def test_llm_routing():
    """Test various user queries with LLM-based routing"""

    # Initialize database and chatbot
    init_db()
    chatbot = ChatbotService()

    # Test cases that don't rely on keywords
    test_queries = [
        {
            "message": "My system isn't producing power anymore",
            "description": "Problem without explicit 'solar' keyword"
        },
        {
            "message": "I need backup power for my home",
            "description": "Purchase intent without 'buy' keyword"
        },
        {
            "message": "What options do you have for renewable energy?",
            "description": "General inquiry about category"
        },
        {
            "message": "The inverter is making a beeping sound",
            "description": "Technical issue with specific equipment"
        },
        {
            "message": "I want to reduce my electricity bill",
            "description": "Goal-based query without product keywords"
        },
        {
            "message": "Can you recommend someone to help with installation?",
            "description": "Service request without 'technician' keyword"
        }
    ]

    print("=" * 80)
    print("LLM-BASED ROUTING TEST")
    print("=" * 80)
    print()

    # Initialize session for testing
    session_state = {
        "state": "ask_questions",
        "temp_data": {}
    }

    user_profile = {
        "name": "Test User",
        "email": "test@example.com"
    }

    for idx, test in enumerate(test_queries, 1):
        print(f"\n{'─' * 80}")
        print(f"TEST {idx}: {test['description']}")
        print(f"{'─' * 80}")
        print(f"User: {test['message']}")
        print()

        try:
            # Process message using the LLM routing
            response = chatbot.process_message(
                user_message=test['message'],
                session_state=session_state,
                user_profile=user_profile,
                conversation_history=[]
            )

            print(f"Bot: {response['bot_message']}")
            print()

            # Show what data was fetched
            recommends = response.get('recommends', {})
            if recommends:
                print("Data fetched:")
                if recommends.get('products'):
                    print(f"  - Products: {len(recommends['products'])} items")
                    for p in recommends['products'][:2]:  # Show first 2
                        print(f"    • {p.get('name', 'N/A')}")

                if recommends.get('technicians'):
                    print(f"  - Technicians: {len(recommends['technicians'])} available")
                    for t in recommends['technicians'][:2]:
                        print(f"    • {t.get('name', 'N/A')} - {t.get('speciality', 'N/A')}")

                if recommends.get('salesman'):
                    print(f"  - Sales Staff: {len(recommends['salesman'])} available")
                    for s in recommends['salesman'][:2]:
                        print(f"    • {s.get('name', 'N/A')} - {s.get('speciality', 'N/A')}")

                if recommends.get('employees'):
                    print(f"  - Employees: {len(recommends['employees'])} found")

            print()
            print(f"Next steps: {', '.join(response.get('next_step', []))}")

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    print()
    print("=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    print("Starting LLM routing test...")
    print()

    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: GOOGLE_API_KEY not found in environment variables")
        print("Please set your Google API key in the .env file")
        sys.exit(1)

    test_llm_routing()
