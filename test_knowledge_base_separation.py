"""
Test to verify bot_message contains only knowledge base info,
while SQL data is passed separately in recommends
"""
import sys
sys.path.append('.')

from app.chatbot_service import ChatbotService
import json

def test_knowledge_base_separation():
    """Test that bot_message uses knowledge base and SQL data is separate"""
    chatbot = ChatbotService()

    print("=" * 80)
    print("Testing Knowledge Base Separation")
    print("=" * 80)

    test_cases = [
        {
            "message": "I want to buy a solar panel",
            "description": "Product search - should fetch products but bot_message should only have guidance"
        },
        {
            "message": "My generator is broken",
            "description": "Technical problem - should fetch technicians but bot_message should only have guidance"
        },
        {
            "message": "Hello",
            "description": "Greeting - no data fetch, only knowledge base response"
        },
        {
            "message": "How do solar panels work?",
            "description": "General question - no data fetch, knowledge base explanation"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"Test {i}: {test_case['description']}")
        print(f"User Message: \"{test_case['message']}\"")
        print(f"{'─' * 80}")

        # Start conversation
        session_state = {"state": "start", "temp_data": {}}

        # Get initial response
        response = chatbot.process_message("", session_state)

        # Choose option 1 (Ask questions)
        session_state = response["session_state"]
        response = chatbot.process_message("1", session_state)

        # Ask the test question
        session_state = response["session_state"]
        response = chatbot.process_message(test_case["message"], session_state)

        # Analyze response
        bot_message = response["bot_message"]
        recommends = response["recommends"]

        print(f"\n📝 BOT MESSAGE (Knowledge Base):")
        print(f"   {bot_message}")

        print(f"\n🗄️  SQL DATA (Separate):")
        has_sql_data = False
        if recommends["products"]:
            has_sql_data = True
            print(f"   ✅ Products: {len(recommends['products'])} items")
            for p in recommends["products"][:2]:  # Show first 2
                print(f"      - {p.get('name', 'N/A')} | ${p.get('price', 'N/A')}")

        if recommends["technicians"]:
            has_sql_data = True
            print(f"   ✅ Technicians: {len(recommends['technicians'])} items")
            for t in recommends["technicians"][:2]:  # Show first 2
                print(f"      - {t.get('name', 'N/A')} | {t.get('speciality', 'N/A')}")

        if recommends["salesman"]:
            has_sql_data = True
            print(f"   ✅ Salesmen: {len(recommends['salesman'])} items")
            for s in recommends["salesman"][:2]:  # Show first 2
                print(f"      - {s.get('name', 'N/A')} | {s.get('speciality', 'N/A')}")

        if not has_sql_data:
            print(f"   ℹ️  No SQL data fetched (as expected for this query)")

        # Validation checks
        print(f"\n✔️  VALIDATION:")

        # Check 1: Bot message should not contain specific numbers/prices
        has_price_in_message = any(char in bot_message for char in ['$', '₹']) or \
                               any(word.isdigit() and len(word) > 2 for word in bot_message.split())
        print(f"   {'✅' if not has_price_in_message else '❌'} Bot message contains no specific prices")

        # Check 2: Bot message should not contain phone numbers
        has_phone = any(word.replace('-', '').replace('.', '').isdigit() and len(word) >= 10
                       for word in bot_message.split())
        print(f"   {'✅' if not has_phone else '❌'} Bot message contains no contact numbers")

        # Check 3: SQL data is in recommends (if applicable)
        if "buy" in test_case["message"].lower() or "broken" in test_case["message"].lower():
            print(f"   {'✅' if has_sql_data else '❌'} SQL data properly fetched in recommends")

        print(f"   {'✅' if bot_message else '❌'} Bot message exists and is not empty")

if __name__ == "__main__":
    test_knowledge_base_separation()
    print("\n" + "=" * 80)
    print("Test completed!")
    print("=" * 80)
