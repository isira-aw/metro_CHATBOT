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
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.3,  # Lower temperature for more consistent routing
            convert_system_message_to_human=True
        )

        # Define available database query functions
        self.tools = self._define_tools()

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
            tool_calls.append({
                "name": "search_products",
                "parameters": {
                    "query": user_message,
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
            tool_calls.append({
                "name": "search_products",
                "parameters": {
                    "query": user_message,
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
            # We have actual data - use it in the response
            prompt += "I have fetched the following relevant data from our database:\n\n"

            for tool_name, data in fetched_data.items():
                if data:
                    prompt += f"=== {tool_name.replace('_', ' ').title()} ===\n"
                    if isinstance(data, list):
                        for idx, item in enumerate(data, 1):
                            prompt += f"{idx}. {json.dumps(item, indent=2)}\n"
                    else:
                        prompt += f"{json.dumps(data, indent=2)}\n"
                    prompt += "\n"

            prompt += """
Now generate a helpful, direct response using the above data.

IMPORTANT:
- Use specific details from the fetched data (product names, specs, prices, technician names, etc.)
- Be direct and answer the question
- If recommending products, mention specific names and key features
- If suggesting technicians/salesmen, provide their names and contact info
- Keep the response concise but informative (2-4 sentences)
- Speak naturally and professionally
"""
        else:
            # No data fetched - this is a conversational message or general question
            prompt += """
This is a general question or conversational message that doesn't require specific database data.

Respond naturally and helpfully:
- If it's a greeting, greet them warmly and briefly introduce yourself as Metro's assistant
- If it's a general question, answer from your knowledge about solar, generators, inverters, electrical systems
- Keep it conversational and friendly
- If appropriate, mention you can help with specific products, technical support, or sales inquiries
- Keep responses concise (1-3 sentences)
"""

        return prompt
