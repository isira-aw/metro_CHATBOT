#!/bin/bash

echo "=================================="
echo "RAG Chatbot Setup Script"
echo "=================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✓ Dependencies installed successfully!"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created. Please edit it with your API keys."
else
    echo ""
    echo "✓ .env file already exists."
fi

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit the .env file with your API keys:"
echo "   - GOOGLE_API_KEY (Gemini API)"
echo "   - PINECONE_API_KEY"
echo "   - PINECONE_ENVIRONMENT"
echo "   - DATABASE_URL"
echo ""
echo "2. Make sure PostgreSQL is running and create the database:"
echo "   createdb chatbot_db"
echo ""
echo "3. Run the application:"
echo "   source venv/bin/activate  # If not already activated"
echo "   python main.py"
echo ""
echo "4. Open your browser to:"
echo "   http://localhost:8000/docs (API Documentation)"
echo "   Or open web_interface.html for the chat interface"
echo ""
echo "5. Run tests:"
echo "   python test_chatbot.py"
echo ""
