from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from app.pinecone_service import PineconeService
from app.database import SessionLocal
from app.database import User, ChatHistory
import os
import re
from datetime import datetime
from typing import Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

class ChatbotService:
    def __init__(self):
        # Initialize Gemini LLM with updated model name
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        
        # Initialize Pinecone service
        self.pinecone_service = PineconeService()
        
        # Create RAG chain
        self._setup_rag_chain()
        
        # Conversation states
        self.STATES = {
            "GREETING": "greeting",
            "WAITING_OPTION": "waiting_option",
            "WAITING_EMAIL_NEW": "waiting_email_new",
            "WAITING_EMAIL_EXISTING": "waiting_email_existing",
            "WAITING_NAME": "waiting_name",
            "WAITING_NUMBER": "waiting_number",
            "ACTIVE_CHAT": "active_chat"
        }
    
    def _setup_rag_chain(self):
        """Setup RAG chain with Pinecone retriever"""
        retriever = self.pinecone_service.get_retriever(k=3)
        
        if retriever is None:
            print("Warning: RAG not available. Will use LLM directly.")
            self.rag_chain = None
            return
        
        prompt_template = """Use the following pieces of context to answer the question at the end. 
        If you don't know the answer from the context, just say that you don't know, don't try to make up an answer.

        Context: {context}

        Question: {question}

        Answer:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        try:
            self.rag_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                chain_type_kwargs={"prompt": PROMPT}
            )
        except Exception as e:
            print(f"Warning: Could not setup RAG chain: {e}")
            self.rag_chain = None
    
    def extract_email(self, text: str) -> str:
        """Extract email from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def extract_phone(self, text: str) -> str:
        """Extract phone number from text"""
        phone_pattern = r'\b\d{10}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        match = re.search(phone_pattern, text)
        return match.group(0).replace('-', '').replace('.', '') if match else None
    
    def extract_name(self, text: str) -> str:
        """Extract name from text (simple extraction)"""
        # Remove common phrases
        text = text.lower()
        text = re.sub(r'my name is |i am |i\'m |name is |this is |name:', '', text, flags=re.IGNORECASE)
        # Extract capitalized words (likely names)
        words = text.split()
        name_words = [word.capitalize() for word in words if len(word) > 1 and word.isalpha()]
        return ' '.join(name_words[:3]) if name_words else None
    
    def check_user_exists(self, email: str) -> User:
        """Check if user exists in database"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            return user
        finally:
            db.close()
    
    def create_user(self, email: str, name: str, mobile_number: str) -> User:
        """Create new user in database"""
        db = SessionLocal()
        try:
            user = User(email=email, name=name, mobile_number=mobile_number)
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()
    
    def save_chat_history(self, email: str, conversation: list):
        """Save chat conversation to database"""
        db = SessionLocal()
        try:
            # Create new chat history record for this conversation
            chat_history = ChatHistory(
                email=email,
                date=datetime.utcnow(),
                conversation=conversation
            )
            db.add(chat_history)
            db.commit()
            print(f"✅ Chat history saved for {email} - {len(conversation)} messages")
        except Exception as e:
            print(f"❌ Error saving chat history: {e}")
            db.rollback()
        finally:
            db.close()
    
    def process_message(self, user_message: str, session_state: Dict = None) -> Tuple[str, Dict]:
        """
        Process user message based on conversation state
        Returns: (bot_response, updated_session_state)
        """
        # Initialize session state if None
        if session_state is None:
            session_state = {
                "state": self.STATES["GREETING"],
                "conversation": []
            }
        
        # Add user message to conversation
        session_state["conversation"].append({"role": "user", "message": user_message})
        
        current_state = session_state.get("state", self.STATES["GREETING"])
        bot_response = ""
        
        # GREETING STATE - Show initial options
        if current_state == self.STATES["GREETING"]:
            bot_response = """Hello there! 👋

Please choose an option:
1) Ask something you want to know from us
2) Do you have an account?
3) Login"""
            session_state["state"] = self.STATES["WAITING_OPTION"]
        
        # WAITING FOR OPTION SELECTION
        elif current_state == self.STATES["WAITING_OPTION"]:
            user_input = user_message.strip()
            
            # Check for option 1 (various inputs)
            if user_input == '1' or user_input.lower() == '1)' or 'option 1' in user_input.lower():
                session_state["state"] = self.STATES["ACTIVE_CHAT"]
                bot_response = "Great! How can I help you today?"
            
            # Check for option 2 (has account)
            elif user_input == '2' or user_input.lower() == '2)' or 'option 2' in user_input.lower():
                session_state["state"] = self.STATES["WAITING_EMAIL_EXISTING"]
                bot_response = "Please enter your email address:"
            
            # Check for option 3 (login)
            elif user_input == '3' or user_input.lower() == '3)' or 'option 3' in user_input.lower():
                session_state["state"] = self.STATES["WAITING_EMAIL_EXISTING"]
                bot_response = "Please enter your email address:"
            
            # Natural language fallback
            elif 'ask' in user_input.lower() and 'option' not in user_input.lower():
                session_state["state"] = self.STATES["ACTIVE_CHAT"]
                bot_response = "Great! How can I help you today?"
            
            elif 'account' in user_input.lower() and 'option' not in user_input.lower():
                session_state["state"] = self.STATES["WAITING_EMAIL_EXISTING"]
                bot_response = "Please enter your email address:"
            
            elif 'login' in user_input.lower() and 'option' not in user_input.lower():
                session_state["state"] = self.STATES["WAITING_EMAIL_EXISTING"]
                bot_response = "Please enter your email address:"
            
            else:
                # Invalid input - show options again
                bot_response = """I didn't understand that. Please type the number of your choice:

1) Ask something you want to know from us
2) Do you have an account?
3) Login"""
                session_state["state"] = self.STATES["WAITING_OPTION"]
        
        # WAITING FOR EMAIL (existing user or new user)
        elif current_state == self.STATES["WAITING_EMAIL_EXISTING"]:
            email = self.extract_email(user_message)
            if email:
                user = self.check_user_exists(email)
                if user:
                    # Existing user - go to active chat
                    session_state["email"] = email
                    session_state["name"] = user.name
                    session_state["state"] = self.STATES["ACTIVE_CHAT"]
                    bot_response = f"Welcome back, {user.name}! How can I help you?"
                    print(f"✅ User logged in: {email}")
                else:
                    # New user - need to register
                    session_state["email"] = email
                    session_state["state"] = self.STATES["WAITING_NAME"]
                    bot_response = "I don't see an account with that email. Let's create one!\n\nPlease enter your name:"
            else:
                bot_response = "I couldn't find a valid email address. Please provide your email:"
        
        # WAITING FOR NAME (new user registration)
        elif current_state == self.STATES["WAITING_NAME"]:
            name = self.extract_name(user_message)
            if name:
                session_state["name"] = name
                session_state["state"] = self.STATES["WAITING_NUMBER"]
                bot_response = f"Nice to meet you, {name}! Please enter your mobile number:"
            else:
                bot_response = "I couldn't get your name. Please tell me your name:"
        
        # WAITING FOR PHONE NUMBER (new user registration)
        elif current_state == self.STATES["WAITING_NUMBER"]:
            phone = self.extract_phone(user_message)
            if phone:
                # Create user in database
                user = self.create_user(
                    email=session_state["email"],
                    name=session_state["name"],
                    mobile_number=phone
                )
                session_state["state"] = self.STATES["ACTIVE_CHAT"]
                bot_response = f"Great! Your account has been created, {session_state['name']}. How can I help you?"
                print(f"✅ New user created: {session_state['email']}")
            else:
                bot_response = "I couldn't get a valid mobile number. Please provide a 10-digit phone number:"
        
        # ACTIVE CHAT - Use RAG to answer questions
        elif current_state == self.STATES["ACTIVE_CHAT"]:
            try:
                # Try RAG first if available
                if self.rag_chain:
                    response = self.rag_chain.invoke({"query": user_message})
                    bot_response = response["result"]
                else:
                    # Fallback to direct LLM if RAG not available
                    bot_response = self.llm.invoke(user_message).content
            except Exception as e:
                # Final fallback
                print(f"Chat error: {e}")
                try:
                    bot_response = self.llm.invoke(user_message).content
                except Exception as llm_error:
                    print(f"LLM error: {llm_error}")
                    bot_response = "I apologize, but I'm having trouble processing your question right now. This might be due to API rate limits. Please try again in a moment, or contact support if the issue persists."
        
        # Add bot response to conversation
        session_state["conversation"].append({"role": "bot", "message": bot_response})
        
        # Save conversation history AFTER bot response is added (only for logged in users in active chat)
        if current_state == self.STATES["ACTIVE_CHAT"] and "email" in session_state:
            try:
                self.save_chat_history(
                    email=session_state["email"],
                    conversation=session_state["conversation"]
                )
            except Exception as e:
                print(f"❌ Error saving chat history: {e}")
        
        return bot_response, session_state
