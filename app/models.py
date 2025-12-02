from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    mobile_number: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    mobile_number: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    user_message: str
    email: Optional[str] = None
    session_state: Optional[Dict] = None

class ChatResponse(BaseModel):
    bot_message: str
    session_state: Optional[Dict] = None

class DocumentUpload(BaseModel):
    text: str
    metadata: Optional[Dict] = None

class DocumentResponse(BaseModel):
    message: str
    chunks_processed: int
