from app.database import SessionLocal, User, Product, Technician, Salesman, Employee, ChatHistory
from typing import Dict, List, Tuple
import re
from datetime import datetime
import json

class ChatbotService:
    def __init__(self):
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

    def search_products(self, query: str, category: str = None) -> List[str]:
        """Search products based on query"""
        db = SessionLocal()
        try:
            products_query = db.query(Product)
            if category:
                products_query = products_query.filter(Product.category.ilike(f"%{category}%"))

            # Search in name and description
            products = products_query.filter(
                (Product.name.ilike(f"%{query}%")) |
                (Product.description.ilike(f"%{query}%"))
            ).limit(3).all()

            return [p.name for p in products] if products else []
        finally:
            db.close()

    def search_technicians(self, speciality: str = None) -> List[Dict[str, str]]:
        """Search technicians by speciality"""
        db = SessionLocal()
        try:
            techs_query = db.query(Technician)
            if speciality:
                techs_query = techs_query.filter(Technician.speciality.ilike(f"%{speciality}%"))

            techs = techs_query.limit(2).all()
            return [{"name": t.name, "speciality": t.speciality, "contact": t.contact} for t in techs]
        finally:
            db.close()

    def search_salesmen(self, speciality: str = None) -> List[Dict[str, str]]:
        """Search salesmen by speciality"""
        db = SessionLocal()
        try:
            sales_query = db.query(Salesman)
            if speciality:
                sales_query = sales_query.filter(Salesman.speciality.ilike(f"%{speciality}%"))

            sales = sales_query.limit(2).all()
            return [{"name": s.name, "speciality": s.speciality, "contact": s.contact} for s in sales]
        finally:
            db.close()

    def analyze_intent(self, message: str) -> Dict[str, any]:
        """Analyze user message to determine intent"""
        message_lower = message.lower()

        # Check for problem/fault keywords
        problem_keywords = ['problem', 'issue', 'fault', 'not working', 'broken', 'repair', 'fix', 'diagnose', 'troubleshoot']
        has_problem = any(kw in message_lower for kw in problem_keywords)

        # Check for buying intent
        buy_keywords = ['buy', 'purchase', 'price', 'cost', 'quote', 'how much', 'want to buy']
        wants_to_buy = any(kw in message_lower for kw in buy_keywords)

        # Identify category
        category = None
        if 'solar' in message_lower:
            category = 'solar'
        elif 'generator' in message_lower:
            category = 'generator'
        elif 'inverter' in message_lower:
            category = 'inverter'
        elif 'electrical' in message_lower or 'electric' in message_lower:
            category = 'electrical'

        return {
            "has_problem": has_problem,
            "wants_to_buy": wants_to_buy,
            "category": category
        }

    def generate_technical_response(self, message: str, intent: Dict, user_profile: Dict = None) -> Tuple[str, Dict, List, str]:
        """
        Generate technical response with recommendations
        Returns: (bot_message, recommends, next_steps, extra_info)
        """
        message_lower = message.lower()

        # Default values
        products = []
        technicians = []
        salesmen = []
        extra_info = ""
        next_steps = ["Ask another question", "View products", "Start over"]

        # Personalize greeting if user profile available
        greeting = f"{user_profile.get('name', 'there')}, " if user_profile else ""

        # Handle based on intent
        if intent["has_problem"]:
            # User has a problem - recommend technician
            technicians = self.search_technicians(intent["category"])

            if intent["category"] == "solar":
                bot_message = f"{greeting}I understand you're having issues with your solar system. Common problems include inverter faults, panel degradation, or wiring issues. I recommend consulting with our specialized technicians."
                extra_info = "A qualified technician can diagnose and resolve your solar system issues."
            elif intent["category"] == "generator":
                bot_message = f"{greeting}Generator issues can range from fuel system problems to electrical faults. Our expert technicians can help diagnose and repair your generator."
                extra_info = "Generator problems should be addressed by experienced technicians for safety."
            elif intent["category"] == "inverter":
                bot_message = f"{greeting}Inverter problems often involve power conversion issues or software glitches. Let me connect you with our inverter specialists."
                extra_info = "Our technicians specialize in inverter troubleshooting and repair."
            else:
                bot_message = f"{greeting}I can help you troubleshoot your issue. Our technicians are available to diagnose and resolve electrical system problems."
                extra_info = "Technical support recommended for proper fault diagnosis."

            if technicians:
                next_steps = ["Contact technician", "Ask another question", "Start over"]

        elif intent["wants_to_buy"]:
            # User wants to buy - recommend salesman and products
            products = self.search_products(message, intent["category"])
            salesmen = self.search_salesmen(intent["category"])

            if intent["category"] == "solar":
                bot_message = f"{greeting}Great! We offer a range of solar systems from 3kW to 50kW. Our solutions include panels, inverters, batteries, and complete installation. Let me recommend some products and connect you with our sales team."
                extra_info = "Our sales staff can provide customized quotes based on your requirements."
            elif intent["category"] == "generator":
                bot_message = f"{greeting}We have various generator options including portable and standby units from 5kW to 500kW. I'll recommend suitable products and our sales specialists can help you choose."
                extra_info = "Sales staff can help determine the right generator size for your needs."
            elif intent["category"] == "inverter":
                bot_message = f"{greeting}We stock inverters from leading brands for solar, UPS, and power backup applications. Our sales team can guide you to the perfect solution."
                extra_info = "Contact our sales team for pricing and availability."
            else:
                bot_message = f"{greeting}I can help you find the right products for your needs. Let me show you some options and connect you with our sales team."
                extra_info = "Our sales staff can provide detailed product information and quotes."

            if salesmen:
                next_steps = ["Contact salesman", "View more products", "Ask another question", "Start over"]

        else:
            # General technical question
            if 'load calculation' in message_lower:
                bot_message = f"{greeting}Load calculation is essential for sizing your electrical system. You need to sum up the wattage of all devices, apply diversity factors, and account for surge loads. Would you like me to connect you with a technician for a detailed assessment?"
                technicians = self.search_technicians("electrical")
                extra_info = "Professional load calculation ensures proper system sizing."

            elif 'solar' in message_lower:
                bot_message = f"{greeting}Solar systems convert sunlight to electricity using photovoltaic panels. Key components include solar panels, inverters, charge controllers, and batteries. System size depends on your energy needs and available roof space. Would you like product recommendations or technical consultation?"
                products = self.search_products("solar", "solar")
                salesmen = self.search_salesmen("solar")
                extra_info = "Solar systems can significantly reduce electricity costs."

            elif 'generator' in message_lower:
                bot_message = f"{greeting}Generators provide backup power during outages. Choose between portable and standby models. Size depends on your power requirements. Key factors include fuel type, runtime, and automatic transfer switches. Need help selecting a generator?"
                products = self.search_products("generator", "generator")
                salesmen = self.search_salesmen("generator")
                extra_info = "Proper generator sizing is crucial for reliable backup power."

            elif 'inverter' in message_lower:
                bot_message = f"{greeting}Inverters convert DC power to AC power. Types include pure sine wave, modified sine wave, and grid-tie inverters. Selection depends on your application - solar, UPS, or power backup. What's your specific need?"
                products = self.search_products("inverter", "inverter")
                salesmen = self.search_salesmen("inverter")
                extra_info = "Inverter selection depends on power requirements and application."

            else:
                bot_message = f"{greeting}I'm here to help with solar systems, generators, inverters, and electrical systems. I can assist with load calculations, fault diagnosis, product selection, and technical support. What would you like to know?"
                next_steps = ["Ask about solar", "Ask about generators", "Ask about inverters", "Start over"]

        recommends = {
            "products": products if products else [],
            "technicians": technicians if technicians else [],
            "salesman": salesmen if salesmen else [],
            "extra_info": extra_info
        }

        return bot_message, recommends, next_steps, extra_info

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
            intent = self.analyze_intent(user_message)
            bot_msg, recommends, next_steps, extra = self.generate_technical_response(
                user_message, intent, user_profile
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
            profile = {"name": user_name} if user_name else None

            intent = self.analyze_intent(user_message)
            bot_msg, recommends, next_steps, extra = self.generate_technical_response(
                user_message, intent, profile
            )
            response["bot_message"] = bot_msg
            response["recommends"] = recommends
            response["next_step"] = next_steps

            # Save chat history if logged in
            if "user_email" in session_state:
                conversation = conversation_history or []
                conversation.append({"user": user_message, "bot": bot_msg, "time": datetime.utcnow().isoformat()})
                self.save_chat_history(session_state["user_email"], conversation)

        # Update session
        session_state["temp_data"] = temp_data
        response["debug"]["session_state"] = session_state
        response["session_state"] = session_state  # Add session_state at top level for frontend access

        return response
