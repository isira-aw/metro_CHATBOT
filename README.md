# RAG Chatbot with LangChain, FastAPI, Gemini, Pinecone & PostgreSQL

A conversational AI chatbot with RAG (Retrieval-Augmented Generation) architecture that manages user authentication, stores chat history, and answers questions using a knowledge base.

## Features

- **Conversational Flow**: Tree-based conversation with user registration/login
- **RAG Architecture**: Uses Pinecone vector database for knowledge retrieval
- **Gemini AI**: Powered by Google's Gemini Pro LLM
- **User Management**: PostgreSQL database for user profiles
- **Chat History**: Stores complete conversation sessions
- **Document Ingestion**: API endpoint to add documents to knowledge base

## Architecture

```
User Input → FastAPI → Chatbot Service → Gemini LLM
                  ↓                           ↓
            PostgreSQL              Pinecone Vector DB
            (Users & Chat)          (Knowledge Base)
```

## Prerequisites

- Python 3.9+
- PostgreSQL database
- Google Gemini API key
- Pinecone account and API key

## Installation

1. **Clone/Extract the project**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
cp .env.example .env
```

Edit `.env` file with your credentials:
```env
GOOGLE_API_KEY=your_gemini_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=chatbot-knowledge
DATABASE_URL=postgresql://username:password@localhost:5432/chatbot_db
```

4. **Set up PostgreSQL database**:
```bash
# Create database
createdb chatbot_db

# Or using psql
psql -U postgres
CREATE DATABASE chatbot_db;
```

5. **Initialize database tables**:
The tables will be created automatically when you start the application.

## Running the Application

Start the FastAPI server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## API Endpoints

### 1. Chat Endpoint
**POST** `/api/chat`

Send messages to the chatbot:

```json
{
  "user_message": "Hello",
  "session_state": null
}
```

Response:
```json
{
  "bot_message": "Hello there! ...",
  "session_state": {
    "state": "initial",
    "conversation": [...]
  }
}
```

### 2. Add Documents
**POST** `/api/documents/add`

Add documents to knowledge base:

```json
{
  "text": "Your document content here...",
  "metadata": {
    "source": "document_name",
    "category": "information"
  }
}
```

### 3. Get All Users
**GET** `/api/users`

### 4. Get User by Email
**GET** `/api/users/{email}`

### 5. Get Chat History
**GET** `/api/chat-history/{email}`

### 6. Create User Manually
**POST** `/api/users`

### 7. Delete User
**DELETE** `/api/users/{email}`

## Conversation Flow

1. **Initial Greeting**:
   - Bot asks: "Hello there! Choose: 1) Ask something 2) Have account 3) Login"

2. **Option 1 - Direct Questions**:
   - User can ask questions immediately
   - Bot uses RAG to answer from knowledge base

3. **Option 2/3 - Login/Register**:
   - **Existing User**: Enter email → Bot greets by name
   - **New User**: Enter email → Enter name → Enter phone → Registration complete

4. **Active Chat**:
   - User asks questions
   - Bot retrieves relevant context from Pinecone
   - Gemini generates answers using retrieved context

## Usage Example

### 1. First Time Chat (Python)

```python
import requests

BASE_URL = "http://localhost:8000"

# Initial message
response = requests.post(f"{BASE_URL}/api/chat", json={
    "user_message": "Hello",
    "session_state": None
})

session_state = response.json()["session_state"]
print(response.json()["bot_message"])

# Choose option 2 (register)
response = requests.post(f"{BASE_URL}/api/chat", json={
    "user_message": "2",
    "session_state": session_state
})

session_state = response.json()["session_state"]
print(response.json()["bot_message"])

# Provide email
response = requests.post(f"{BASE_URL}/api/chat", json={
    "user_message": "isira123@gmail.com",
    "session_state": session_state
})

session_state = response.json()["session_state"]
print(response.json()["bot_message"])

# Provide name
response = requests.post(f"{BASE_URL}/api/chat", json={
    "user_message": "Isira Adithya",
    "session_state": session_state
})

session_state = response.json()["session_state"]
print(response.json()["bot_message"])

# Provide phone number
response = requests.post(f"{BASE_URL}/api/chat", json={
    "user_message": "0710540195",
    "session_state": session_state
})

session_state = response.json()["session_state"]
print(response.json()["bot_message"])

# Ask question
response = requests.post(f"{BASE_URL}/api/chat", json={
    "user_message": "What services do you offer?",
    "session_state": session_state
})

print(response.json()["bot_message"])
```

### 2. Add Documents to Knowledge Base

```python
import requests

response = requests.post("http://localhost:8000/api/documents/add", json={
    "text": """
    Our company offers various services including:
    - AI Consulting
    - Machine Learning Solutions
    - Data Analytics
    - Cloud Infrastructure Setup
    
    We specialize in helping businesses leverage AI technology.
    """,
    "metadata": {
        "source": "services_document",
        "category": "company_info"
    }
})

print(response.json())
```

### 3. Using cURL

```bash
# Chat
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_message": "Hello", "session_state": null}'

# Add document
curl -X POST "http://localhost:8000/api/documents/add" \
  -H "Content-Type: application/json" \
  -d '{"text": "Your document content", "metadata": {"source": "test"}}'

# Get chat history
curl "http://localhost:8000/api/chat-history/isira123@gmail.com"
```

## Database Schema

### Users Table
- `id`: Integer (Primary Key)
- `email`: String (Unique)
- `name`: String
- `mobile_number`: String
- `created_at`: DateTime

### Chat History Table
- `id`: Integer (Primary Key)
- `email`: String (Foreign Key)
- `date`: DateTime
- `conversation`: JSON (Array of messages)

## Project Structure

```
chatbot_project/
├── main.py                 # FastAPI application
├── chatbot_service.py      # Chatbot logic & conversation flow
├── pinecone_service.py     # Pinecone vector database operations
├── database.py             # SQLAlchemy models & database setup
├── models.py               # Pydantic models for validation
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Key Components

1. **ChatbotService**: Manages conversation flow, user registration, and RAG queries
2. **PineconeService**: Handles document embedding, storage, and retrieval
3. **Database Models**: SQLAlchemy models for users and chat history
4. **FastAPI Routes**: RESTful API endpoints

## Troubleshooting

### Pinecone Connection Issues
- Verify API key and environment in `.env`
- Check if index exists in Pinecone dashboard
- Ensure correct dimension (768 for Gemini embeddings)

### Database Connection
- Verify PostgreSQL is running
- Check DATABASE_URL format
- Ensure database exists

### Gemini API Errors
- Verify GOOGLE_API_KEY is valid
- Check API quota limits
- Review Gemini API documentation

## Features in Detail

### RAG (Retrieval-Augmented Generation)
- Documents are split into chunks (1000 chars, 200 overlap)
- Chunks are embedded using Gemini embeddings
- Stored in Pinecone vector database
- Retrieved based on similarity to user query
- Fed to Gemini LLM as context for answers

### Session Management
- Session state tracks conversation progress
- Maintains user context across messages
- Stores conversation history in JSON format

### Smart Extraction
- Email extraction using regex
- Phone number extraction (10 digits)
- Name extraction from natural text

## Security Notes

- Store API keys in environment variables
- Use HTTPS in production
- Implement rate limiting
- Add authentication for sensitive endpoints
- Validate all user inputs

## License

MIT License

## Support

For issues or questions, please contact support or check the API documentation at `/docs`.
