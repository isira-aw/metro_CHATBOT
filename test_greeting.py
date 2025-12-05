"""
Quick test to verify greetings don't trigger unnecessary database queries
"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.chatbot_service import ChatbotService
from app.database import init_db

def test_greetings():
    """Test that greetings work naturally without fetching data"""

    init_db()
    chatbot = ChatbotService()

    test_cases = [
        "Hello",
        "Hi there",
        "Good morning",
        "What is solar energy?",
        "How do generators work?",
        "I need a 10kW solar system",  # This SHOULD fetch data
    ]

    session_state = {"state": "ask_questions", "temp_data": {}}

    for test_msg in test_cases:
        print(f"\n{'='*60}")
        print(f"User: {test_msg}")
        print(f"{'='*60}")

        response = chatbot.process_message(
            user_message=test_msg,
            session_state=session_state,
            user_profile=None,
            conversation_history=[]
        )

        print(f"Bot: {response['bot_message']}")

        # Check what data was fetched
        recommends = response.get('recommends', {})
        data_fetched = any([
            recommends.get('products'),
            recommends.get('technicians'),
            recommends.get('salesman'),
            recommends.get('employees')
        ])

        if data_fetched:
            print(f"✓ Data fetched: Products={len(recommends.get('products', []))}, "
                  f"Technicians={len(recommends.get('technicians', []))}, "
                  f"Salesmen={len(recommends.get('salesman', []))}")
        else:
            print(f"✓ No data fetched (conversational response)")

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ ERROR: GOOGLE_API_KEY not found")
        sys.exit(1)

    test_greetings()
