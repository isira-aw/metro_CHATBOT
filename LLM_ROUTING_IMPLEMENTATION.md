# LLM-Based Database Routing Implementation

## Overview

This implementation replaces the keyword-based chatbot routing with an intelligent LLM-powered system that:

1. **Analyzes** user questions using natural language understanding
2. **Decides** which database queries are needed (products, technicians, salesmen, employees)
3. **Fetches** relevant data from the database
4. **Generates** contextual responses using actual data

## Key Changes

### Before (Keyword-Based)
- Used hardcoded keyword matching (e.g., "solar", "generator", "buy", "problem")
- Generic responses like "I'm here to help with solar systems..."
- Limited understanding of user intent
- Could not handle nuanced queries

### After (LLM-Based)
- Uses Google's Gemini LLM to understand user intent
- Intelligently decides what data to fetch
- Provides specific, data-driven responses
- Handles complex queries without explicit keywords

## Architecture

### New Files

#### `app/llm_service.py`
The core LLM routing engine with:
- **Tool definitions**: Describes available database queries to the LLM
- **Plan and execute**: Two-phase approach
  - Phase 1: LLM decides what data to fetch
  - Phase 2: LLM generates response using fetched data
- **Database executor pattern**: Calls methods on ChatbotService to fetch data

### Modified Files

#### `app/chatbot_service.py`
Updated to use LLM routing:
- Added `LLMService` initialization
- Enhanced database methods to return detailed data
- New method: `generate_llm_response()` - replaces keyword-based routing
- Removed: `analyze_intent()` and `generate_technical_response()`

## Database Query Tools

The LLM can call these functions to fetch data:

1. **search_products**: Find products by query and category
2. **search_technicians**: Find technicians by specialty
3. **search_salesmen**: Find sales staff by specialty
4. **search_employees**: Find employees by department/position
5. **get_user_history**: Retrieve user's chat history (if logged in)

## Example Usage

### Example 1: Problem Without Keywords
**User**: "My system isn't producing power anymore"

**LLM Analysis**:
- Detects problem/fault intent
- Recognizes it's likely about solar/electrical systems
- Calls: `search_technicians(specialty="solar")`

**Response**: Uses actual technician data from database

### Example 2: Purchase Intent Without "Buy"
**User**: "I need backup power for my home"

**LLM Analysis**:
- Understands backup power need → generator or solar+battery
- Calls: `search_products(query="backup power")`, `search_salesmen(specialty="generator")`

**Response**: Recommends specific products with names and specs

### Example 3: Goal-Based Query
**User**: "I want to reduce my electricity bill"

**LLM Analysis**:
- Maps goal to solar systems
- Calls: `search_products(category="solar")`, `search_salesmen(specialty="solar")`

**Response**: Explains how solar reduces costs + recommends specific systems

## Testing

Run the test script to validate LLM routing:

```bash
python test_llm_routing.py
```

This tests various queries that don't rely on keywords:
- "My system isn't producing power anymore"
- "I need backup power for my home"
- "What options do you have for renewable energy?"
- "The inverter is making a beeping sound"
- "I want to reduce my electricity bill"
- "Can you recommend someone to help with installation?"

## Configuration

Requires `GOOGLE_API_KEY` in `.env` file:

```env
GOOGLE_API_KEY=your_api_key_here
DATABASE_URL=your_database_url
```

## Benefits

1. **Natural Conversations**: Users can ask questions naturally without specific keywords
2. **Accurate Routing**: LLM understands intent better than keyword matching
3. **Data-Driven**: Responses include actual product names, specs, and contact info
4. **No Generic Messages**: Eliminates "I'm here to help" type responses
5. **Extensible**: Easy to add new database query tools
6. **Context-Aware**: Uses conversation history for better understanding

## Flow Diagram

```
User Query
    ↓
LLM Analysis (Gemini)
    ↓
Determine Required Data
    ↓
Execute Database Queries
    ↓
Fetch: Products, Technicians, Salesmen, etc.
    ↓
LLM Response Generation
    ↓
Contextual Response with Specific Data
```

## Future Enhancements

1. **Function Calling API**: Use native Gemini function calling instead of heuristics
2. **Embeddings**: Add vector search for better product matching
3. **Multi-turn Planning**: Allow LLM to ask clarifying questions
4. **Caching**: Cache common queries for faster responses
5. **A/B Testing**: Compare LLM routing vs keyword performance
