# Metro Chatbot - Technical Support System

A FastAPI-based chatbot for technical support in solar systems, generators, inverters, and electrical systems. The chatbot provides technical help, manages company data, and makes intelligent recommendations based on user queries.

## Features

- **Technical Support**: Help with solar systems, generators, inverters, and electrical systems
- **Smart Recommendations**: Suggests products, technicians, and sales staff based on user needs
- **User Management**: Account creation and login system
- **Company Data Management**: Manage products, technicians, salesmen, and employees
- **Conversation History**: Stores all conversations for logged-in users
- **Strict JSON Format**: All responses follow a consistent JSON structure
- **Personalization**: Uses user profile and conversation history

## Architecture

```
User → FastAPI → Chatbot Service
                      ↓
                 PostgreSQL
          (Users, Products, Technicians,
           Salesmen, Employees, Chat History)
```

## Prerequisites

- Python 3.9+
- PostgreSQL database

## Installation

1. **Clone the repository**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
Create a `.env` file:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/metro_chatbot
APP_HOST=0.0.0.0
APP_PORT=8000
```

4. **Set up PostgreSQL database**:
```bash
createdb metro_chatbot
```

## Running the Application

Start the server:
```bash
python main.py
```

Or using uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Access the API:
- API: `http://localhost:8000`
- Documentation: `http://localhost:8000/docs`

## API Endpoints

### Chat Endpoint

**POST** `/api/chat`

The main chatbot endpoint. Always returns JSON in the specified format.

**Request:**
```json
{
  "user_message": "I have a solar panel problem",
  "session_state": {},
  "user_profile": {
    "name": "John",
    "email": "john@example.com",
    "phone": "1234567890"
  },
  "conversation_history": []
}
```

**Response:**
```json
{
  "bot_message": "I understand you're having issues with your solar system...",
  "recommends": {
    "products": [],
    "technicians": [
      {
        "name": "Alex",
        "speciality": "Solar Systems",
        "contact": "0771234567"
      }
    ],
    "salesman": [],
    "extra_info": "A qualified technician can diagnose and resolve your solar system issues."
  },
  "next_step": [
    "Contact technician",
    "Ask another question",
    "Start over"
  ],
  "debug": {
    "state": "active_chat",
    "timestamp": "2025-12-04T10:00:00Z"
  }
}
```

### Product Management

- **POST** `/api/products` - Create a product
- **GET** `/api/products` - Get all products (filter by `?category=solar`)
- **GET** `/api/products/{id}` - Get product by ID
- **PUT** `/api/products/{id}` - Update a product
- **DELETE** `/api/products/{id}` - Delete a product

**Create Product Example:**
```json
{
  "name": "5kW Solar System",
  "category": "solar",
  "description": "Complete 5kW solar system with panels, inverter, and mounting",
  "specifications": {
    "power": "5kW",
    "panels": "10x 500W",
    "inverter": "5kW hybrid"
  },
  "price": 5000.00
}
```

### Technician Management

- **POST** `/api/technicians` - Create a technician
- **GET** `/api/technicians` - Get all technicians (filter by `?speciality=solar`)
- **GET** `/api/technicians/{id}` - Get technician by ID
- **PUT** `/api/technicians/{id}` - Update a technician
- **DELETE** `/api/technicians/{id}` - Delete a technician

**Create Technician Example:**
```json
{
  "name": "Alex Johnson",
  "speciality": "Solar Systems",
  "contact": "0771234567",
  "email": "alex@example.com",
  "experience_years": 5
}
```

### Salesman Management

- **POST** `/api/salesmen` - Create a salesman
- **GET** `/api/salesmen` - Get all salesmen (filter by `?speciality=solar`)
- **GET** `/api/salesmen/{id}` - Get salesman by ID
- **PUT** `/api/salesmen/{id}` - Update a salesman
- **DELETE** `/api/salesmen/{id}` - Delete a salesman

**Create Salesman Example:**
```json
{
  "name": "Sahan Perera",
  "speciality": "Solar",
  "contact": "0771234567",
  "email": "sahan@example.com"
}
```

### Employee Management

- **POST** `/api/employees` - Create an employee
- **GET** `/api/employees` - Get all employees (filter by `?department=technical`)
- **GET** `/api/employees/{id}` - Get employee by ID
- **PUT** `/api/employees/{id}` - Update an employee
- **DELETE** `/api/employees/{id}` - Delete an employee

### User Management

- **POST** `/api/users` - Create a user
- **GET** `/api/users` - Get all users
- **GET** `/api/users/{email}` - Get user by email
- **DELETE** `/api/users/{email}` - Delete a user

### Chat History

- **GET** `/api/chat-history/{email}` - Get chat history for a user

## Conversation Flow

### 1. Start
```
Bot: "Hello there,
1) Ask some questions
2) Create an account
3) Log in"
```

### 2. Option 1 - Ask Questions
User can ask technical questions without login. Bot provides:
- Technical explanations
- Product recommendations
- Technician/salesman recommendations based on need

### 3. Option 2 - Create Account
```
Bot: "Please enter your email:"
User: "john@example.com"
Bot: "Please enter your name:"
User: "John Doe"
Bot: "Please enter your mobile number:"
User: "1234567890"
Bot: "John Doe, your account has been created! How can I help you?"
```

### 4. Option 3 - Login
```
Bot: "Please enter your email:"
User: "john@example.com"
Bot: "Welcome back John Doe, how can I help you?"
```

### 5. Active Chat
Once logged in or in "Ask Questions" mode, users can:
- Ask about solar systems, generators, inverters, electrical systems
- Get load calculations help
- Request product recommendations
- Get connected with technicians for problems
- Get connected with salesmen for purchases

## Recommendation Logic

The chatbot intelligently recommends based on user intent:

### When user has a problem:
- **Recommends**: Technicians matching the category
- **Example**: "My generator is not starting" → Recommends generator technicians

### When user wants to buy:
- **Recommends**: Products and Salesmen matching the category
- **Example**: "I want to buy a solar system" → Recommends solar products and solar sales staff

### General technical questions:
- **Provides**: Technical explanations
- **May recommend**: Products, technicians, or salesmen based on context

## Database Schema

### Users
- id, email (unique), name, mobile_number, created_at

### Products
- id, name, category, description, specifications (JSON), price, created_at

### Technicians
- id, name, speciality, contact, email, experience_years, created_at

### Salesmen
- id, name, speciality, contact, email, created_at

### Employees
- id, name, position, department, contact, email, created_at

### Chat History
- id, email (FK), date, conversation (JSON)

## Usage Examples

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Add sample products
requests.post(f"{BASE_URL}/api/products", json={
    "name": "10kW Solar System Complete Package",
    "category": "solar",
    "description": "Complete 10kW solar system with 20x500W panels, 10kW hybrid inverter, and 10kWh battery",
    "price": 8500.00
})

# Add sample technician
requests.post(f"{BASE_URL}/api/technicians", json={
    "name": "Alex Johnson",
    "speciality": "Solar Systems",
    "contact": "0771234567",
    "experience_years": 5
})

# Add sample salesman
requests.post(f"{BASE_URL}/api/salesmen", json={
    "name": "Sahan Perera",
    "speciality": "Solar",
    "contact": "0771234567"
})

# Start chat
response = requests.post(f"{BASE_URL}/api/chat", json={
    "user_message": "Hello"
})
print(response.json())

# Choose option 1 (ask questions)
session = response.json()["debug"]["session_state"]
response = requests.post(f"{BASE_URL}/api/chat", json={
    "user_message": "1",
    "session_state": session
})
print(response.json())

# Ask about solar
session = response.json()["debug"]["session_state"]
response = requests.post(f"{BASE_URL}/api/chat", json={
    "user_message": "I want to buy a solar system for my home",
    "session_state": session
})
print(response.json())
# This will recommend products and salesmen
```

### cURL Example

```bash
# Add a product
curl -X POST "http://localhost:8000/api/products" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "5kW Solar System",
    "category": "solar",
    "description": "Complete 5kW solar system",
    "price": 5000.00
  }'

# Chat
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "I have a generator problem"
  }'
```

## Project Structure

```
metro_CHATBOT/
├── app/
│   ├── chatbot_service.py    # Chatbot logic and conversation flow
│   ├── database.py            # SQLAlchemy models
│   └── models.py              # Pydantic models
├── main.py                    # FastAPI application
├── requirements.txt           # Dependencies
├── .env                       # Environment variables
└── README.md                  # This file
```

## Key Features

### 1. Intent Analysis
The chatbot analyzes user messages to determine:
- Problem/fault keywords → Recommend technician
- Buying intent keywords → Recommend products and salesman
- Category (solar, generator, inverter, electrical)

### 2. Personalization
- Uses user name in responses when available
- Stores conversation history for logged-in users
- Maintains session state across messages

### 3. Data-Driven Recommendations
- Searches internal database for matching products
- Finds technicians by speciality
- Connects users with appropriate salesmen

### 4. Strict JSON Format
All responses follow the exact format:
```json
{
  "bot_message": "string",
  "recommends": {
    "products": ["string"],
    "technicians": [{"name": "", "speciality": "", "contact": ""}],
    "salesman": [{"name": "", "speciality": "", "contact": ""}],
    "extra_info": "string"
  },
  "next_step": ["string"],
  "debug": {}
}
```

## Categories Supported

- **Solar**: Solar panels, solar systems, solar inverters, solar batteries
- **Generator**: Portable generators, standby generators, diesel generators
- **Inverter**: Pure sine wave inverters, UPS inverters, hybrid inverters
- **Electrical**: Electrical systems, wiring, load calculations, fault diagnosis

## Technical Support Topics

- Load calculations
- Fault diagnosis and troubleshooting
- System sizing and selection
- Product specifications
- Installation guidance
- Maintenance advice

## Security Notes

- Store DATABASE_URL in environment variables
- Use HTTPS in production
- Implement authentication for sensitive endpoints
- Add rate limiting for chat endpoint
- Validate all user inputs

## License

MIT License

## Support

For API documentation, visit: `http://localhost:8000/docs`
