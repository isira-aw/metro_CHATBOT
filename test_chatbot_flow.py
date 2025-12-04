#!/usr/bin/env python3
"""
Test script to verify chatbot menu flow without running the full server
"""
import sys
import json

# Mock the database dependencies
class MockDB:
    def query(self, *args): return self
    def filter(self, *args): return self
    def first(self): return None
    def add(self, *args): pass
    def commit(self): pass
    def refresh(self, *args): pass
    def close(self): pass

class MockUser:
    def __init__(self):
        self.email = None
        self.name = None
        self.mobile_number = None

# Patch the database before importing
sys.modules['app.database'] = type('module', (), {
    'SessionLocal': lambda: MockDB(),
    'User': MockUser,
    'Product': type('Product', (), {}),
    'Technician': type('Technician', (), {}),
    'Salesman': type('Salesman', (), {}),
    'Employee': type('Employee', (), {}),
    'ChatHistory': type('ChatHistory', (), {})
})()

# Now import the chatbot service
from app.chatbot_service import ChatbotService

def test_menu_flow():
    """Test the complete menu flow"""
    chatbot = ChatbotService()

    print("=" * 60)
    print("Testing Chatbot Menu Flow")
    print("=" * 60)

    # Test 1: Initial message (START state)
    print("\n1. User types: 'hello'")
    response1 = chatbot.process_message("hello")
    print(f"Bot responds: {response1['bot_message']}")
    print(f"State after: {response1['session_state']['state']}")
    assert "1) Ask some questions" in response1['bot_message']
    assert response1['session_state']['state'] == 'waiting_option'
    print("✓ PASS: Initial menu shown, state changed to waiting_option")

    # Test 2: User selects option 1 (Ask questions)
    print("\n2. User types: '1'")
    response2 = chatbot.process_message("1", session_state=response1['session_state'])
    print(f"Bot responds: {response2['bot_message']}")
    print(f"State after: {response2['session_state']['state']}")
    assert "Ask your questions" in response2['bot_message']
    assert response2['session_state']['state'] == 'ask_questions'
    print("✓ PASS: Entered ask questions mode")

    # Reset for test 3
    print("\n" + "-" * 60)

    # Test 3: Create account flow
    print("\n3. User types: 'hello' (restart)")
    response3 = chatbot.process_message("hello")
    assert response3['session_state']['state'] == 'waiting_option'

    print("\n4. User types: '2'")
    response4 = chatbot.process_message("2", session_state=response3['session_state'])
    print(f"Bot responds: {response4['bot_message']}")
    print(f"State after: {response4['session_state']['state']}")
    assert "email" in response4['bot_message'].lower()
    assert response4['session_state']['state'] == 'create_account_email'
    print("✓ PASS: Entered create account flow")

    print("\n5. User enters email: 'test@example.com'")
    response5 = chatbot.process_message("test@example.com", session_state=response4['session_state'])
    print(f"Bot responds: {response5['bot_message']}")
    print(f"State after: {response5['session_state']['state']}")
    assert "name" in response5['bot_message'].lower()
    assert response5['session_state']['state'] == 'create_account_name'
    print("✓ PASS: Asked for name")

    print("\n6. User enters name: 'John Doe'")
    response6 = chatbot.process_message("John Doe", session_state=response5['session_state'])
    print(f"Bot responds: {response6['bot_message']}")
    print(f"State after: {response6['session_state']['state']}")
    assert "mobile" in response6['bot_message'].lower()
    assert response6['session_state']['state'] == 'create_account_mobile'
    print("✓ PASS: Asked for mobile number")

    # Reset for test 4
    print("\n" + "-" * 60)

    # Test 4: Login flow
    print("\n7. User types: 'hello' (restart)")
    response7 = chatbot.process_message("hello")

    print("\n8. User types: '3'")
    response8 = chatbot.process_message("3", session_state=response7['session_state'])
    print(f"Bot responds: {response8['bot_message']}")
    print(f"State after: {response8['session_state']['state']}")
    assert "email" in response8['bot_message'].lower()
    assert response8['session_state']['state'] == 'login_email'
    print("✓ PASS: Entered login flow")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ✓")
    print("=" * 60)
    print("\nThe chatbot menu flow is working correctly!")
    print("Session state is properly maintained between messages.")
    return True

if __name__ == "__main__":
    try:
        test_menu_flow()
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
