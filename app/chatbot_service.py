from app.database import SessionLocal, User, Product, Technician, Salesman, Employee, ChatHistory
from app.llm_service import LLMService
from app.classification_service import ClassificationService
from typing import Dict, List, Tuple, Optional
import re
from datetime import datetime
import json

class ChatbotService:
    def __init__(self):
        # Initialize LLM service for intelligent routing
        try:
            self.llm_service = LLMService()
        except Exception as e:
            print(f"Warning: LLM service initialization failed: {e}")
            self.llm_service = None

        # Initialize classification service for category prediction
        try:
            self.classifier = ClassificationService()
            print("✓ Classification service initialized")
        except Exception as e:
            print(f"Warning: Classification service initialization failed: {e}")
            self.classifier = None

        # Conversation states
        self.STATES = {
            "START": "start",
            "WAITING_OPTION": "waiting_option",
            "ASK_QUESTIONS": "ask_questions",
            "CREATE_ACCOUNT_EMAIL": "create_account_email",
            "CREATE_ACCOUNT_NAME": "create_account_name",
            "CREATE_ACCOUNT_MOBILE": "create_account_mobile",
            "LOGIN_EMAIL": "login_email",
            "ACTIVE_CHAT": "active_chat"
        }

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
        """Extract name from text"""
        text = text.strip()
        # Remove common phrases
        text = re.sub(r'my name is |i am |i\'m |name is |this is |name:', '', text, flags=re.IGNORECASE)
        # Clean and capitalize
        words = text.split()
        name_words = [word.capitalize() for word in words if len(word) > 1 and word.isalpha()]
        return ' '.join(name_words[:3]) if name_words else None

    def get_user(self, email: str) -> User:
        """Get user from database"""
        db = SessionLocal()
        try:
            return db.query(User).filter(User.email == email).first()
        finally:
            db.close()

    def create_user(self, email: str, name: str, mobile_number: str) -> User:
        """Create new user"""
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
        """Save chat conversation"""
        db = SessionLocal()
        try:
            chat_history = ChatHistory(
                email=email,
                date=datetime.utcnow(),
                conversation=conversation
            )
            db.add(chat_history)
            db.commit()
        except Exception as e:
            print(f"Error saving chat: {e}")
            db.rollback()
        finally:
            db.close()

    def search_products(self, query: str, category: str = None, max_results: int = 5) -> List[Dict]:
        """Search products based on query - Returns detailed product information"""
        db = SessionLocal()
        try:
            products_query = db.query(Product)
            if category:
                products_query = products_query.filter(Product.category.ilike(f"%{category}%"))

            # Search in name and description
            products = products_query.filter(
                (Product.name.ilike(f"%{query}%")) |
                (Product.description.ilike(f"%{query}%"))
            ).limit(max_results).all()

            return [{
                "name": p.name,
                "category": p.category,
                "description": p.description,
                "specifications": p.specifications,
                "price": p.price
            } for p in products] if products else []
        finally:
            db.close()

    def search_technicians(self, specialty: str = "", max_results: int = 3) -> List[Dict[str, str]]:
        """Search technicians by specialty"""
        db = SessionLocal()
        try:
            techs_query = db.query(Technician)
            if specialty:
                techs_query = techs_query.filter(Technician.speciality.ilike(f"%{specialty}%"))

            techs = techs_query.limit(max_results).all()
            return [{
                "name": t.name,
                "speciality": t.speciality,
                "contact": t.contact,
                "email": t.email if t.email else "",
                "experience_years": str(t.experience_years) if t.experience_years else "0"
            } for t in techs]
        finally:
            db.close()

    def search_salesmen(self, specialty: str = "", max_results: int = 3) -> List[Dict[str, str]]:
        """Search salesmen by specialty"""
        db = SessionLocal()
        try:
            sales_query = db.query(Salesman)
            if specialty:
                sales_query = sales_query.filter(Salesman.speciality.ilike(f"%{specialty}%"))

            sales = sales_query.limit(max_results).all()
            return [{
                "name": s.name,
                "speciality": s.speciality,
                "contact": s.contact,
                "email": s.email if s.email else ""
            } for s in sales]
        finally:
            db.close()

    def search_employees(self, department: str = "", position: str = "", max_results: int = 3) -> List[Dict[str, str]]:
        """Search employees by department or position"""
        db = SessionLocal()
        try:
            emp_query = db.query(Employee)
            if department:
                emp_query = emp_query.filter(Employee.department.ilike(f"%{department}%"))
            if position:
                emp_query = emp_query.filter(Employee.position.ilike(f"%{position}%"))

            employees = emp_query.limit(max_results).all()
            return [{
                "name": e.name,
                "position": e.position,
                "department": e.department,
                "contact": e.contact,
                "email": e.email if e.email else ""
            } for e in employees]
        finally:
            db.close()

    def get_user_history(self, user_email: str, limit: int = 5) -> List[Dict]:
        """Get user's chat history"""
        db = SessionLocal()
        try:
            history = db.query(ChatHistory).filter(
                ChatHistory.email == user_email
            ).order_by(ChatHistory.date.desc()).limit(limit).all()

            return [{
                "date": h.date.isoformat(),
                "conversation": h.conversation
            } for h in history]
        finally:
            db.close()

    def generate_llm_response(self, message: str, user_profile: Dict = None, conversation_history: List = None) -> Tuple[str, Dict, List]:
        """
        Generate response using TF-IDF classification and LLM-based routing
        Returns: (bot_message, recommends, next_steps)
        """
        if not self.llm_service:
            # Fallback if LLM service is not available
            return (
                "I apologize, but the intelligent response system is currently unavailable. Please try again later.",
                {"products": [], "technicians": [], "salesman": [], "employees": [], "extra_info": ""},
                ["Try again", "Start over"]
            )

        try:
            # Step 1: Classify the user message into a category
            category = "common"
            confidence_scores = {}

            if self.classifier:
                category, confidence_scores = self.classifier.classify(message)
                print(f"📊 Category: {category} (confidence: {confidence_scores.get(category, 0):.2f})")

            # Step 2: Use LLM service to plan and execute database queries
            result = self.llm_service.plan_and_execute(
                user_message=message,
                conversation_history=conversation_history,
                user_profile=user_profile,
                database_executor=self,  # Pass self as executor so LLM can call our methods
                category=category,  # Pass the predicted category
                category_confidence=confidence_scores
            )

            bot_message = result.get("bot_message", "I'm not sure how to respond to that.")
            fetched_data = result.get("fetched_data", {})

            # Step 3: Build recommends structure from fetched data
            recommends = {
                "products": fetched_data.get("search_products", []),
                "technicians": fetched_data.get("search_technicians", []),
                "salesman": fetched_data.get("search_salesmen", []),
                "employees": fetched_data.get("search_employees", []),
                "extra_info": ""
            }

            # Step 4: Filter recommendations based on category (limit to 1-2 suggestions)
            if self.classifier:
                max_recommendations = self.classifier.get_max_recommendations(category)

                # Limit each recommendation list to max_recommendations
                if max_recommendations > 0:
                    recommends["products"] = recommends["products"][:max_recommendations]
                    recommends["technicians"] = recommends["technicians"][:max_recommendations]
                    recommends["salesman"] = recommends["salesman"][:max_recommendations]
                    recommends["employees"] = recommends["employees"][:max_recommendations]
                else:
                    # For 'common' category, don't show recommendations
                    recommends["products"] = []
                    recommends["technicians"] = []
                    recommends["salesman"] = []
                    recommends["employees"] = []

                # Add category info to extra_info
                recommends["extra_info"] = f"Category: {category}"

            # Step 5: Generate next steps based on category and fetched data
            next_steps = ["Ask another question"]
            if recommends["products"]:
                next_steps.append("View more products")
            if recommends["technicians"]:
                next_steps.append("Contact technician")
            if recommends["salesman"]:
                next_steps.append("Contact sales")
            if recommends["employees"]:
                next_steps.append("View employee details")
            next_steps.append("Start over")

            return bot_message, recommends, next_steps

        except Exception as e:
            print(f"Error in LLM response generation: {e}")
            import traceback
            traceback.print_exc()
            return (
                "I apologize, but I encountered an error processing your question. Could you please rephrase?",
                {"products": [], "technicians": [], "salesman": [], "employees": [], "extra_info": ""},
                ["Try again", "Start over"]
            )

    def process_message(self, user_message: str, session_state: Dict = None,
                       user_profile: Dict = None, conversation_history: List = None) -> Dict:
        """
        Process user message and return JSON response
        Returns strict JSON format as specified
        """
        # Initialize session
        if session_state is None:
            session_state = {
                "state": self.STATES["START"],
                "temp_data": {}
            }

        current_state = session_state.get("state", self.STATES["START"])
        temp_data = session_state.get("temp_data", {})

        # Default response structure
        response = {
            "bot_message": "",
            "recommends": {
                "products": [],
                "technicians": [],
                "salesman": [],
                "extra_info": ""
            },
            "next_step": [],
            "debug": {
                "state": current_state,
                "user_profile": user_profile,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        # START STATE
        if current_state == self.STATES["START"]:
            response["bot_message"] = "Hello there,\n1) Ask some questions\n2) Create an account\n3) Log in"
            response["next_step"] = ["Option 1", "Option 2", "Option 3"]
            session_state["state"] = self.STATES["WAITING_OPTION"]

        # WAITING FOR OPTION
        elif current_state == self.STATES["WAITING_OPTION"]:
            choice = user_message.strip()

            if choice in ['1', '1)', 'option 1', 'ask questions', 'ask some questions']:
                response["bot_message"] = "Ask your questions."
                response["next_step"] = ["Ask about solar", "Ask about generators", "Ask about inverters", "Ask about electrical systems"]
                session_state["state"] = self.STATES["ASK_QUESTIONS"]

            elif choice in ['2', '2)', 'option 2', 'create account', 'create an account']:
                response["bot_message"] = "Let's create an account for you.\n\nPlease enter your email:"
                response["next_step"] = []
                session_state["state"] = self.STATES["CREATE_ACCOUNT_EMAIL"]

            elif choice in ['3', '3)', 'option 3', 'log in', 'login']:
                response["bot_message"] = "Please enter your email to log in:"
                response["next_step"] = []
                session_state["state"] = self.STATES["LOGIN_EMAIL"]

            else:
                response["bot_message"] = "Please choose a valid option:\n1) Ask some questions\n2) Create an account\n3) Log in"
                response["next_step"] = ["Option 1", "Option 2", "Option 3"]

        # ASK QUESTIONS (No login required)
        elif current_state == self.STATES["ASK_QUESTIONS"]:
            bot_msg, recommends, next_steps = self.generate_llm_response(
                user_message, user_profile, conversation_history
            )
            response["bot_message"] = bot_msg
            response["recommends"] = recommends
            response["next_step"] = next_steps

        # CREATE ACCOUNT - EMAIL
        elif current_state == self.STATES["CREATE_ACCOUNT_EMAIL"]:
            email = self.extract_email(user_message)
            if email:
                # Check if user exists
                existing = self.get_user(email)
                if existing:
                    response["bot_message"] = f"This email is already registered. Welcome back, {existing.name}!\n\nHow can I help you?"
                    session_state["state"] = self.STATES["ACTIVE_CHAT"]
                    session_state["user_email"] = email
                    session_state["user_name"] = existing.name
                    response["next_step"] = ["Ask a question", "View products", "Contact support"]
                else:
                    temp_data["email"] = email
                    response["bot_message"] = "Great! Now, please enter your name:"
                    response["next_step"] = []
                    session_state["state"] = self.STATES["CREATE_ACCOUNT_NAME"]
            else:
                response["bot_message"] = "I couldn't find a valid email. Please enter your email address:"
                response["next_step"] = []

        # CREATE ACCOUNT - NAME
        elif current_state == self.STATES["CREATE_ACCOUNT_NAME"]:
            name = self.extract_name(user_message)
            if name:
                temp_data["name"] = name
                response["bot_message"] = f"Nice to meet you, {name}! Please enter your mobile number:"
                response["next_step"] = []
                session_state["state"] = self.STATES["CREATE_ACCOUNT_MOBILE"]
            else:
                response["bot_message"] = "Please enter your name:"
                response["next_step"] = []

        # CREATE ACCOUNT - MOBILE
        elif current_state == self.STATES["CREATE_ACCOUNT_MOBILE"]:
            phone = self.extract_phone(user_message)
            if phone:
                # Create user
                user = self.create_user(temp_data["email"], temp_data["name"], phone)
                response["bot_message"] = f"{temp_data['name']}, your account has been created! How can I help you?"
                response["next_step"] = ["Ask a question", "View products", "Contact support"]
                session_state["state"] = self.STATES["ACTIVE_CHAT"]
                session_state["user_email"] = temp_data["email"]
                session_state["user_name"] = temp_data["name"]
                temp_data.clear()
            else:
                response["bot_message"] = "Please enter a valid mobile number (10 digits):"
                response["next_step"] = []

        # LOGIN
        elif current_state == self.STATES["LOGIN_EMAIL"]:
            email = self.extract_email(user_message)
            if email:
                user = self.get_user(email)
                if user:
                    response["bot_message"] = f"Welcome back {user.name}, how can I help you?"
                    response["next_step"] = ["Ask a question", "View products", "Contact support"]
                    session_state["state"] = self.STATES["ACTIVE_CHAT"]
                    session_state["user_email"] = email
                    session_state["user_name"] = user.name
                else:
                    response["bot_message"] = "No account found with that email. Would you like to create an account?\n\n1) Yes, create account\n2) Try different email"
                    response["next_step"] = ["Create account", "Try again"]
                    session_state["state"] = self.STATES["WAITING_OPTION"]
            else:
                response["bot_message"] = "Please enter a valid email address:"
                response["next_step"] = []

        # ACTIVE CHAT (Logged in)
        elif current_state == self.STATES["ACTIVE_CHAT"]:
            user_name = session_state.get("user_name", "")
            user_email = session_state.get("user_email", "")
            profile = {
                "name": user_name,
                "email": user_email
            } if user_name else None

            bot_msg, recommends, next_steps = self.generate_llm_response(
                user_message, profile, conversation_history
            )
            response["bot_message"] = bot_msg
            response["recommends"] = recommends
            response["next_step"] = next_steps

            # Save chat history if logged in
            if user_email:
                conversation = conversation_history or []
                conversation.append({"user": user_message, "bot": bot_msg, "time": datetime.utcnow().isoformat()})
                self.save_chat_history(user_email, conversation)

        # Update session
        session_state["temp_data"] = temp_data
        response["debug"]["session_state"] = session_state
        response["session_state"] = session_state  # Add session_state at top level for frontend access

        return response
