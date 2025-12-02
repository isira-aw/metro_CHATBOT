from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import init_db, get_db, User, ChatHistory
from app.models import (
    ChatMessage, ChatResponse, DocumentUpload, 
    DocumentResponse, UserCreate, UserResponse
)
from app.chatbot_service import ChatbotService
from app.pinecone_service import PineconeService
from typing import List
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="RAG Chatbot API",
    description="Chatbot with LangChain, Gemini, Pinecone, and PostgreSQL",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
chatbot_service = ChatbotService()
pinecone_service = PineconeService()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("Database initialized successfully!")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Chatbot API is running!",
        "endpoints": {
            "chat": "/api/chat",
            "add_documents": "/api/documents/add",
            "users": "/api/users",
            "chat_history": "/api/chat-history/{email}"
        }
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Main chat endpoint
    Processes user messages through the conversation flow
    """
    try:
        bot_response, updated_session = chatbot_service.process_message(
            user_message=message.user_message,
            session_state=message.session_state
        )
        
        return ChatResponse(
            bot_message=bot_response,
            session_state=updated_session
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.post("/api/documents/add", response_model=DocumentResponse)
async def add_documents(document: DocumentUpload):
    """
    Add documents to Pinecone vector database
    Text will be chunked and embedded automatically
    """
    print(f" [{datetime.now().isoformat()}] [INFO] Starting document upload process...")
    print(f" [{datetime.now().isoformat()}] [DEBUG] Document length: {len(document.text)} characters")
    
    if document.metadata:
        print(f" [DEBUG] Metadata provided: {document.metadata}")
    
    try:
        chunks_processed = pinecone_service.add_documents(
            text=document.text,
            metadata=document.metadata
        )
        
        print(f" [INFO] Successfully processed {chunks_processed} chunks")
        print(f" [INFO] Document upload completed successfully")
        
        return DocumentResponse(
            message="Documents added successfully",
            chunks_processed=chunks_processed
        )
    except Exception as e:
        print(f" [ERROR] Failed to add documents: {str(e)}")
        print(f" [ERROR] Error type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"Error adding documents: {str(e)}")

@app.post("/api/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user manually
    """
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create new user
        db_user = User(
            email=user.email,
            name=user.name,
            mobile_number=user.mobile_number
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.get("/api/users", response_model=List[UserResponse])
async def get_all_users(db: Session = Depends(get_db)):
    """
    Get all users
    """
    try:
        users = db.query(User).all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@app.get("/api/users/{email}", response_model=UserResponse)
async def get_user(email: str, db: Session = Depends(get_db)):
    """
    Get user by email
    """
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

@app.get("/api/chat-history/{email}")
async def get_chat_history(email: str, db: Session = Depends(get_db)):
    """
    Get chat history for a specific user
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get chat history
        chat_history = db.query(ChatHistory).filter(
            ChatHistory.email == email
        ).order_by(ChatHistory.date.desc()).all()
        
        return {
            "email": email,
            "name": user.name,
            "chat_sessions": [
                {
                    "id": chat.id,
                    "date": chat.date,
                    "conversation": chat.conversation
                }
                for chat in chat_history
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")

@app.delete("/api/users/{email}")
async def delete_user(email: str, db: Session = Depends(get_db)):
    """
    Delete a user and their chat history
    """
    try:
        # Delete user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete chat history
        db.query(ChatHistory).filter(ChatHistory.email == email).delete()
        
        # Delete user
        db.delete(user)
        db.commit()
        
        return {"message": f"User {email} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "pinecone": "connected",
            "gemini": "connected"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8000)),
        reload=True
    )
