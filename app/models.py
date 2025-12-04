from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# User Models
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

# Product Models
class ProductCreate(BaseModel):
    name: str
    category: str  # solar, generator, inverter, electrical
    description: str
    specifications: Optional[Dict] = None
    price: Optional[float] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    description: str
    specifications: Optional[Dict] = None
    price: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Technician Models
class TechnicianCreate(BaseModel):
    name: str
    speciality: str  # Solar Systems, Generators, Inverters, Electrical Systems, etc.
    contact: str
    email: Optional[EmailStr] = None
    experience_years: Optional[int] = None

class TechnicianResponse(BaseModel):
    id: int
    name: str
    speciality: str
    contact: str
    email: Optional[str] = None
    experience_years: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Salesman Models
class SalesmanCreate(BaseModel):
    name: str
    speciality: str  # Solar, Generator, Inverter, General
    contact: str
    email: Optional[EmailStr] = None

class SalesmanResponse(BaseModel):
    id: int
    name: str
    speciality: str
    contact: str
    email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Employee Models
class EmployeeCreate(BaseModel):
    name: str
    position: str
    department: str
    contact: str
    email: Optional[EmailStr] = None

class EmployeeResponse(BaseModel):
    id: int
    name: str
    position: str
    department: str
    contact: str
    email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Chat Models
class ChatMessage(BaseModel):
    user_message: str
    session_state: Optional[Dict] = None
    user_profile: Optional[Dict] = None  # name, email, phone
    conversation_history: Optional[List[Dict]] = None

class Recommends(BaseModel):
    products: List[str]
    technicians: List[Dict[str, str]]
    salesman: List[Dict[str, str]]
    extra_info: str

class ChatResponse(BaseModel):
    bot_message: str
    recommends: Recommends
    next_step: List[str]
    debug: Dict[str, Any]
