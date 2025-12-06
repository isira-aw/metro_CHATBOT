"""
LLM Service for intelligent database routing and response generation.
Uses Google's Gemini with function calling to decide what data to fetch.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from typing import Dict, List, Optional, Any
import os
from dotenv import load_dotenv
import json

load_dotenv()


class LLMService:
    def __init__(self):
        """Initialize the LLM service with Gemini"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        # Initialize Gemini with function calling support
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.3,  # Lower temperature for more consistent routing
            convert_system_message_to_human=True
        )

        # Define available database query functions
        self.tools = self._define_tools()

    def extract_search_keywords(self, user_message: str) -> str:
        """
        Extract relevant search keywords from user message using LLM
        Returns cleaned keywords suitable for database searching
        """
        try:
            prompt = f"""Extract the key search terms from this user message that would be useful for searching a product database.

User message: "{user_message}"

Rules:
- Extract only the most relevant product-related keywords
- Include technical specifications (e.g., "10kW", "5000W")
- Include product types (e.g., "solar panel", "generator", "inverter")
- Remove filler words ("I need", "I want", "Can you show me", etc.)
- Return only the keywords separated by spaces
- Maximum 5 keywords

Examples:
Input: "I need a 10kW solar panel for my home to reduce electricity bills"
Output: "10kW solar panel"

Input: "Can you show me generators that can power a house during outages?"
Output: "generator house power"

Input: "What inverters do you have?"
Output: "inverter"

Now extract keywords from the user message above. Return ONLY the keywords, nothing else."""

            response = self.llm.invoke([HumanMessage(content=prompt)])
            keywords = response.content.strip()

            # If extraction failed or returned empty, fall back to simple extraction
            if not keywords or len(keywords) < 2:
                # Simple fallback: extract words that look like products or specs
                words = user_message.lower().split()
                product_words = ['solar', 'generator', 'inverter', 'panel', 'battery', 'electrical']
                keywords = ' '.join([w for w in words if any(pw in w for pw in product_words) or any(c.isdigit() for c in w)])
                if not keywords:
                    keywords = user_message  # Last resort: use full message

            return keywords

        except Exception as e:
            print(f"Error extracting keywords: {e}")
            # Fallback to original message if extraction fails
            return user_message

    def _define_tools(self) -> List[Dict]:
        """Define the database query tools available to the LLM"""
        return [
            {
                "name": "search_products",
                "description": "Search for products in the database. Use this when user asks about products, pricing, or wants to buy something. Returns product details including name, description, category, specifications, and price.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search term to find in product name or description (e.g., 'solar panel', '10kW generator', 'inverter')"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["solar", "generator", "inverter", "electrical"],
                            "description": "Product category to filter by. Use if user mentions a specific category."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of products to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_technicians",
                "description": "Search for technicians by specialty. Use this when user has technical problems, needs repairs, troubleshooting, or fault diagnosis. Returns technician details including name, specialty, contact, and experience.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "specialty": {
                            "type": "string",
                            "description": "Technician specialty to search for (e.g., 'solar', 'generator', 'electrical', 'inverter'). Leave empty to get all technicians."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of technicians to return (default: 3)",
                            "default": 3
                        }
                    }
                }
            },
            {
                "name": "search_salesmen",
                "description": "Search for sales staff by specialty. Use this when user wants to buy products, get quotes, or needs sales consultation. Returns salesman details including name, specialty, and contact.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "specialty": {
                            "type": "string",
                            "description": "Sales specialty to search for (e.g., 'solar', 'generator', 'electrical'). Leave empty to get all salesmen."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of salesmen to return (default: 3)",
                            "default": 3
                        }
                    }
                }
            },
            {
                "name": "search_employees",
                "description": "Search for company employees by department or position. Use this when user needs to contact specific departments or roles. Returns employee details including name, position, department, and contact.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "department": {
                            "type": "string",
                            "description": "Department to search in (e.g., 'technical', 'sales', 'support', 'management')"
                        },
                        "position": {
                            "type": "string",
                            "description": "Position/role to search for (e.g., 'manager', 'engineer', 'supervisor')"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of employees to return (default: 3)",
                            "default": 3
                        }
                    }
                }
            },
            {
                "name": "get_user_history",
                "description": "Get user's previous chat conversations. Use this when user asks about their previous conversations or history. Only works if user is logged in.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Number of recent conversations to retrieve (default: 5)",
                            "default": 5
                        }
                    }
                }
            }
        ]

    def get_system_prompt(self, user_profile: Optional[Dict] = None) -> str:
        """Generate system prompt for the LLM"""
        user_context = ""
        if user_profile:
            user_context = f"\nUser Profile: {user_profile.get('name', 'Guest')} (Email: {user_profile.get('email', 'Not logged in')})"

        return f"""You are a helpful technical assistant for Metro, a company specializing in solar systems, generators, inverters, and electrical systems.

Your job is to:
1. Analyze the user's message to understand their intent
2. Determine if you need specific data from the database to answer properly
3. Only fetch data when the user needs specific information (products, contacts, technical help)
4. Respond naturally and conversationally when appropriate

CRITICAL - When to fetch data vs when NOT to:
- DON'T fetch data for: greetings, general questions, explanations, or casual conversation
- DO fetch data when user needs: specific products, pricing, technical support contacts, sales help, or has a problem to solve

IMPORTANT GUIDELINES:
- Be conversational and natural - respond to greetings appropriately
- Only fetch database data when user asks for something specific
- If user has a technical problem/fault → search for technicians
- If user wants to buy specific products/get quotes → search for products and salesmen
- If user asks general questions about how things work → answer from knowledge, no data needed
- Use specific data from database when you do fetch it
- Keep responses helpful and concise
- Use the user's name if available{user_context}

Available data sources (use only when needed):
- Products: Solar panels, generators, inverters, electrical equipment with specs and pricing
- Technicians: Specialists for repairs, troubleshooting, and technical support
- Salesmen: Sales staff for product recommendations and quotes
- Employees: Company staff organized by department and position
"""

    def plan_and_execute(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        user_profile: Optional[Dict] = None,
        database_executor: Optional[Any] = None
    ) -> Dict:
        """
        Main method: LLM decides what data to fetch, executes queries, then generates response

        Args:
            user_message: The user's question/message
            conversation_history: Previous messages in the conversation
            user_profile: User profile info (name, email, etc.)
            database_executor: Object with methods to execute database queries

        Returns:
            Dict with bot_message and fetched data
        """
        # Build conversation context
        messages = [
            SystemMessage(content=self.get_system_prompt(user_profile))
        ]

        # Add conversation history (last 5 messages for context)
        if conversation_history:
            for msg in conversation_history[-5:]:
                if msg.get("user"):
                    messages.append(HumanMessage(content=msg["user"]))
                if msg.get("bot"):
                    messages.append(AIMessage(content=msg["bot"]))

        # Add current message
        messages.append(HumanMessage(content=user_message))

        # Phase 1: Let LLM decide what data to fetch (with function calling)
        try:
            # First LLM call: routing decision
            routing_prompt = f"""Analyze this user message and decide what data you need to fetch from the database to answer properly.

User message: "{user_message}"

Think about:
1. Is the user asking about products? (search_products)
2. Does the user have a technical problem? (search_technicians)
3. Does the user want to buy something? (search_salesmen, search_products)
4. Does the user need to contact a specific department? (search_employees)
5. Is the user asking about their history? (get_user_history - only if logged in)

Based on your analysis, call the appropriate tool(s) to fetch the data you need. You can call multiple tools if needed.
If the question is general knowledge about solar/generators/etc that doesn't require specific product data, you can answer directly without calling tools."""

            routing_messages = [
                SystemMessage(content=self.get_system_prompt(user_profile)),
                HumanMessage(content=routing_prompt)
            ]

            # Get LLM's decision on what to fetch
            # Note: For function calling, we'll use a simpler approach with structured output
            response = self.llm.invoke(routing_messages)

            # Parse the response to determine what data to fetch
            # This is a simplified version - in production, you'd use proper function calling
            tool_calls = self._parse_tool_calls(response.content, user_message)

            # Phase 2: Execute the database queries
            fetched_data = {}
            if database_executor and tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    tool_params = tool_call["parameters"]

                    if hasattr(database_executor, tool_name):
                        try:
                            result = getattr(database_executor, tool_name)(**tool_params)
                            fetched_data[tool_name] = result
                        except Exception as e:
                            print(f"Error executing {tool_name}: {e}")
                            fetched_data[tool_name] = []

            # Phase 3: Generate final response using the fetched data
            final_prompt = self._build_final_prompt(user_message, fetched_data, user_profile)
            final_messages = [
                SystemMessage(content=self.get_system_prompt(user_profile)),
                HumanMessage(content=final_prompt)
            ]

            final_response = self.llm.invoke(final_messages)

            return {
                "bot_message": final_response.content,
                "fetched_data": fetched_data,
                "tool_calls": tool_calls
            }

        except Exception as e:
            print(f"Error in LLM routing: {e}")
            return {
                "bot_message": "I apologize, but I'm having trouble processing your request. Could you please rephrase your question?",
                "fetched_data": {},
                "tool_calls": [],
                "error": str(e)
            }

    def _parse_tool_calls(self, llm_response: str, user_message: str) -> List[Dict]:
        """
        Parse LLM response to extract tool calls.
        This is a simplified heuristic-based approach.
        In production, use proper function calling APIs.
        """
        tool_calls = []
        user_lower = user_message.lower().strip()

        # First, check if this is a greeting or general conversation - NO DATA NEEDED
        greeting_patterns = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
                           'greetings', 'howdy', 'what\'s up', 'whats up', 'sup']
        general_questions = ['how are you', 'who are you', 'what can you do', 'help me',
                           'what is this', 'thank you', 'thanks', 'bye', 'goodbye']

        # If it's just a greeting or very short general message, don't fetch data
        if any(user_lower.startswith(pattern) for pattern in greeting_patterns) or \
           any(pattern in user_lower for pattern in general_questions) or \
           len(user_lower.split()) <= 2:  # Very short messages
            return []  # No data needed for conversational messages

        # Check for general "how does X work" or "what is X" questions - answer from knowledge
        knowledge_patterns = ['how does', 'how do', 'what is', 'what are', 'explain', 'tell me about']
        if any(pattern in user_lower for pattern in knowledge_patterns) and \
           not any(word in user_lower for word in ['recommend', 'suggest', 'need', 'want', 'price', 'cost', 'buy']):
            # General knowledge question, no specific product needed
            return []

        # Now check for specific intents that require data
        problem_keywords = ['problem', 'issue', 'fault', 'not working', 'broken', 'repair', 'fix',
                          'diagnose', 'troubleshoot', 'error', 'failing', 'stopped working']
        buy_keywords = ['buy', 'purchase', 'price', 'cost', 'quote', 'how much', 'want to buy',
                       'looking for', 'need', 'want', 'recommend', 'suggest', 'shopping for']
        product_keywords = ['solar', 'generator', 'inverter', 'panel', 'battery', 'product',
                          'equipment', 'system']

        has_problem = any(kw in user_lower for kw in problem_keywords)
        wants_to_buy = any(kw in user_lower for kw in buy_keywords)
        mentions_product = any(kw in user_lower for kw in product_keywords)

        # Determine category
        category = None
        if 'solar' in user_lower:
            category = 'solar'
        elif 'generator' in user_lower:
            category = 'generator'
        elif 'inverter' in user_lower:
            category = 'inverter'
        elif 'electrical' in user_lower or 'electric' in user_lower:
            category = 'electrical'

        # Build tool calls based on intent
        if has_problem:
            # User has a problem - fetch technicians
            tool_calls.append({
                "name": "search_technicians",
                "parameters": {
                    "specialty": category if category else "",
                    "max_results": 3
                }
            })

        if wants_to_buy:
            # User wants to buy - fetch products and salesmen
            # Extract keywords for better product search
            search_keywords = self.extract_search_keywords(user_message)
            tool_calls.append({
                "name": "search_products",
                "parameters": {
                    "query": search_keywords,
                    "category": category,
                    "max_results": 5
                }
            })
            tool_calls.append({
                "name": "search_salesmen",
                "parameters": {
                    "specialty": category if category else "",
                    "max_results": 2
                }
            })
        elif mentions_product and not has_problem:
            # Just asking about products, not buying yet
            # Extract keywords for better product search
            search_keywords = self.extract_search_keywords(user_message)
            tool_calls.append({
                "name": "search_products",
                "parameters": {
                    "query": search_keywords,
                    "category": category,
                    "max_results": 3
                }
            })

        return tool_calls

    def _build_final_prompt(
        self,
        user_message: str,
        fetched_data: Dict,
        user_profile: Optional[Dict] = None
    ) -> str:
        """Build the final prompt with fetched data for response generation"""

        prompt = f"User asked: \"{user_message}\"\n\n"

        if user_profile:
            prompt += f"User profile: {user_profile.get('name', 'Guest')}\n\n"

        if fetched_data and any(fetched_data.values()):
            # We have actual data - use TWO-PHASE RESPONSE approach
            prompt += "I have fetched the following relevant data from our database:\n\n"

            has_results = False
            empty_searches = []

            for tool_name, data in fetched_data.items():
                if data and len(data) > 0:
                    has_results = True
                    prompt += f"=== {tool_name.replace('_', ' ').title()} ===\n"
                    if isinstance(data, list):
                        for idx, item in enumerate(data, 1):
                            prompt += f"{idx}. {json.dumps(item, indent=2)}\n"
                    else:
                        prompt += f"{json.dumps(data, indent=2)}\n"
                    prompt += "\n"
                else:
                    empty_searches.append(tool_name.replace('_', ' '))

            if empty_searches:
                prompt += f"\n⚠️ NOTE: No results found for: {', '.join(empty_searches)}\n"
                prompt += "You should acknowledge this and offer alternatives or suggestions.\n\n"

            prompt += """
CRITICAL - Use a TWO-PHASE RESPONSE structure:

📋 PHASE 1 - Answer the Question (Using Your Knowledge):
- First, provide a helpful, accurate answer to their question using your AI knowledge
- Explain the concept, solution, or provide relevant information
- Be educational and informative
- This should be 2-3 sentences of valuable information
- DO NOT mention database results yet

🎯 PHASE 2 - Database Recommendations (Based on Our Data):
- After answering, present relevant database results as specific recommendations
- Use this format based on what data you have:

  If products found:
  "Based on our inventory, I recommend:
  • [Product Name] - [Key specs] - [Price]
  • [Product Name] - [Key specs] - [Price]"

  If technicians found:
  "I can connect you with our specialists:
  • [Name] - [Specialty] - Contact: [Contact]"

  If salesmen found:
  "Our sales team can help:
  • [Name] - [Specialty] - Contact: [Contact]"

EXAMPLE RESPONSE:
"Solar panels convert sunlight into electricity using photovoltaic cells. A 10kW system typically covers a medium-sized home's energy needs and can reduce your electricity bills by 70-90%. The installation usually takes 1-2 days depending on roof type.

Based on our inventory, I recommend:
• SunPower 10kW Solar System - High efficiency monocrystalline panels, 25-year warranty - $12,500
• Canadian Solar 10.5kW Kit - Durable polycrystalline design, great value - $9,800

Our solar specialists can help you:
• John Smith - Solar Installation Expert - Contact: 555-0123"

IMPORTANT RULES:
- Always do Phase 1 first (answer with knowledge)
- Then Phase 2 (present database recommendations)
- Use specific details from database (names, prices, specs)
- If empty results in a category, skip that section
- Keep total response 4-6 sentences
- Be natural and professional

HANDLING EMPTY RESULTS:
If some searches returned no results, acknowledge it professionally and offer alternatives:
"I don't currently have [product/specialist] in our database, but I can:
1. Check with our team and get back to you
2. Suggest similar alternatives
3. Connect you with our general sales/technical team who can help"

Example: "While I don't have specific 15kW solar systems in our current inventory, we do have 10kW and 20kW options that might work. Our solar specialists can also custom-design a system for your needs."
"""
        else:
            # No data fetched - still provide helpful knowledge-based response
            prompt += """
No database data was needed for this query. Provide a helpful response using your knowledge.

STRUCTURE:
1. If greeting: Greet warmly + introduce yourself as Metro's AI assistant for solar, generators, and electrical systems
2. If general question: Answer accurately using your knowledge about:
   - Solar systems (panels, inverters, batteries, installation)
   - Generators (types, sizing, fuel types, applications)
   - Inverters (pure sine wave, modified sine wave, sizing)
   - Electrical systems (wiring, safety, maintenance)

3. Then briefly mention what you CAN help with:
   "I can help you find specific products, connect you with technicians, or answer technical questions about [relevant topic]."

EXAMPLE RESPONSES:

User: "Hi there"
Response: "Hello! I'm Metro's AI assistant, here to help you with solar systems, generators, inverters, and electrical solutions. I can help you find products, connect with specialists, or answer any technical questions you have. What would you like to know?"

User: "How does an inverter work?"
Response: "An inverter converts DC (direct current) electricity from batteries or solar panels into AC (alternating current) that your home appliances use. Pure sine wave inverters provide clean power suitable for sensitive electronics, while modified sine wave inverters are more affordable but better for simple devices like lights and fans. I can help you find the right inverter for your needs or connect you with our technical team for installation advice."

User: "What's better, solar or generator?"
Response: "It depends on your needs! Solar is great for long-term savings and eco-friendly power, with no fuel costs but dependent on sunlight. Generators provide reliable backup power anytime but require fuel and maintenance. Many people use both - solar for daily use and a generator as backup. I can recommend specific systems based on your power needs and budget."

RULES:
- Answer accurately using technical knowledge
- Be helpful and educational
- Keep it concise (2-3 sentences)
- Mention relevant services you can provide
- Stay professional and friendly
"""

        return prompt
