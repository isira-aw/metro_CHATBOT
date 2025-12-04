#!/usr/bin/env python3
"""
Simple test to verify chatbot menu navigation works
"""
import sys

# Mock the database dependencies completely
class MockDB:
    def query(self, *args): return self
    def filter(self, *args): return self
    def first(self): return None
    def all(self): return []
    def limit(self, *args): return self
    def ilike(self, *args): return True
    def add(self, *args): pass
    def commit(self): pass
    def refresh(self, *args): pass
    def close(self): pass

# Patch everything before importing
sys.modules['app.database'] = type('module', (), {
    'SessionLocal': lambda: MockDB(),
    'User': type('User', (), {}),
    'Product': type('Product', (), {}),
    'Technician': type('Technician', (), {}),
    'Salesman': type('Salesman', (), {}),
    'Employee': type('Employee', (), {}),
    'ChatHistory': type('ChatHistory', (), {})
})()

from app.chatbot_service import ChatbotService

def test_menu_navigation():
    """Test that menu options properly change state"""
    chatbot = ChatbotService()

    print("=" * 70)
    print("TESTING CHATBOT MENU NAVIGATION")
    print("=" * 70)

    # Test START -> Option 1
    print("\n" + "─" * 70)
    print("TEST 1: Initial Menu Display")
    print("─" * 70)
    response = chatbot.process_message("hello")
    print(f"User: hello")
    print(f"Bot: {response['bot_message'][:50]}...")
    print(f"State: {response['session_state']['state']}")

    assert "1) Ask some questions" in response['bot_message'], "Menu should be shown"
    assert response['session_state']['state'] == 'waiting_option', "Should be in waiting_option state"
    print("✓ PASS: Menu displayed, state = waiting_option")

    # Test Option 1: Ask Questions
    print("\n" + "─" * 70)
    print("TEST 2: Select Option 1 (Ask Questions)")
    print("─" * 70)
    response2 = chatbot.process_message("1", session_state=response['session_state'])
    print(f"User: 1")
    print(f"Bot: {response2['bot_message']}")
    print(f"State: {response2['session_state']['state']}")

    assert response2['session_state']['state'] == 'ask_questions', "Should transition to ask_questions"
    assert "Ask your questions" in response2['bot_message'], "Should prompt for questions"
    print("✓ PASS: Transitioned to ask_questions state")

    # Test Option 2: Create Account (from fresh start)
    print("\n" + "─" * 70)
    print("TEST 3: Select Option 2 (Create Account)")
    print("─" * 70)
    response3 = chatbot.process_message("hello")  # Fresh start
    response4 = chatbot.process_message("2", session_state=response3['session_state'])
    print(f"User: 2")
    print(f"Bot: {response4['bot_message'][:50]}...")
    print(f"State: {response4['session_state']['state']}")

    assert response4['session_state']['state'] == 'create_account_email', "Should transition to create_account_email"
    assert "email" in response4['bot_message'].lower(), "Should ask for email"
    print("✓ PASS: Transitioned to create_account_email state")

    # Test Option 3: Login (from fresh start)
    print("\n" + "─" * 70)
    print("TEST 4: Select Option 3 (Login)")
    print("─" * 70)
    response5 = chatbot.process_message("hello")  # Fresh start
    response6 = chatbot.process_message("3", session_state=response5['session_state'])
    print(f"User: 3")
    print(f"Bot: {response6['bot_message']}")
    print(f"State: {response6['session_state']['state']}")

    assert response6['session_state']['state'] == 'login_email', "Should transition to login_email"
    assert "email" in response6['bot_message'].lower(), "Should ask for email"
    print("✓ PASS: Transitioned to login_email state")

    # Test invalid option
    print("\n" + "─" * 70)
    print("TEST 5: Invalid Option")
    print("─" * 70)
    response7 = chatbot.process_message("hello")  # Fresh start
    response8 = chatbot.process_message("99", session_state=response7['session_state'])
    print(f"User: 99")
    print(f"Bot: {response8['bot_message'][:60]}...")
    print(f"State: {response8['session_state']['state']}")

    assert response8['session_state']['state'] == 'waiting_option', "Should stay in waiting_option"
    assert "valid option" in response8['bot_message'].lower() or "choose" in response8['bot_message'].lower()
    print("✓ PASS: Stays in waiting_option for invalid input")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED! ✓✓✓")
    print("=" * 70)
    print("\nSummary:")
    print("  • Menu is displayed on initial message")
    print("  • Option 1 correctly transitions to 'Ask Questions' mode")
    print("  • Option 2 correctly starts 'Create Account' flow")
    print("  • Option 3 correctly starts 'Login' flow")
    print("  • Invalid options are handled gracefully")
    print("\n✓ The chatbot menu navigation is working correctly!")
    print("✓ Session state is properly maintained between messages!")

    return True

if __name__ == "__main__":
    try:
        test_menu_navigation()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗✗✗ TEST FAILED ✗✗✗")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗✗✗ ERROR ✗✗✗")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
