from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import (
    init_db, get_db, User, ChatHistory, Product,
    Technician, Salesman, Employee
)
from app.models import (
    ChatMessage, ChatResponse, UserCreate, UserResponse,
    ProductCreate, ProductResponse, TechnicianCreate, TechnicianResponse,
    SalesmanCreate, SalesmanResponse, EmployeeCreate, EmployeeResponse,
    DocumentAdd, DocumentAddResponse
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
    title="Metro Chatbot API",
    description="Technical chatbot for solar systems, generators, inverters, and electrical systems",
    version="2.0.0"
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
        "message": "Metro Chatbot API is running!",
        "version": "2.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "users": "/api/users",
            "products": "/api/products",
            "technicians": "/api/technicians",
            "salesmen": "/api/salesmen",
            "employees": "/api/employees",
            "documents": "/api/documents/add"
        }
    }

# ==================== CHAT ENDPOINT ====================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Main chat endpoint - Always returns JSON in specified format

    Request:
    {
        "user_message": "string",
        "session_state": {},  // optional
        "user_profile": {},   // optional
        "conversation_history": []  // optional
    }

    Response:
    {
        "bot_message": "string",
        "recommends": {
            "products": [],
            "technicians": [],
            "salesman": [],
            "extra_info": ""
        },
        "next_step": [],
        "debug": {}
    }
    """
    try:
        response = chatbot_service.process_message(
            user_message=message.user_message,
            session_state=message.session_state,
            user_profile=message.user_profile,
            conversation_history=message.conversation_history
        )
        return response
    except Exception as e:
        # Even errors should return JSON format
        return {
            "bot_message": "I apologize, but I encountered an error processing your request. Please try again.",
            "recommends": {
                "products": [],
                "technicians": [],
                "salesman": [],
                "extra_info": ""
            },
            "next_step": ["Start over"],
            "debug": {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        }

# ==================== USER MANAGEMENT ====================

@app.post("/api/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

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
    """Get all users"""
    try:
        users = db.query(User).all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@app.get("/api/users/{email}", response_model=UserResponse)
async def get_user(email: str, db: Session = Depends(get_db)):
    """Get user by email"""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

@app.delete("/api/users/{email}")
async def delete_user(email: str, db: Session = Depends(get_db)):
    """Delete a user"""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db.query(ChatHistory).filter(ChatHistory.email == email).delete()
        db.delete(user)
        db.commit()
        return {"message": f"User {email} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

# ==================== PRODUCT MANAGEMENT ====================

@app.post("/api/products", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Create a new product"""
    try:
        db_product = Product(
            name=product.name,
            category=product.category,
            description=product.description,
            specifications=product.specifications,
            price=product.price
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")

@app.get("/api/products", response_model=List[ProductResponse])
async def get_all_products(category: str = None, db: Session = Depends(get_db)):
    """Get all products, optionally filter by category"""
    try:
        query = db.query(Product)
        if category:
            query = query.filter(Product.category.ilike(f"%{category}%"))
        products = query.all()
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@app.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product by ID"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")

@app.put("/api/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    """Update a product"""
    try:
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")

        db_product.name = product.name
        db_product.category = product.category
        db_product.description = product.description
        db_product.specifications = product.specifications
        db_product.price = product.price

        db.commit()
        db.refresh(db_product)
        return db_product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        db.delete(product)
        db.commit()
        return {"message": f"Product {product_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")

# ==================== TECHNICIAN MANAGEMENT ====================

@app.post("/api/technicians", response_model=TechnicianResponse)
async def create_technician(technician: TechnicianCreate, db: Session = Depends(get_db)):
    """Create a new technician"""
    try:
        db_technician = Technician(
            name=technician.name,
            speciality=technician.speciality,
            contact=technician.contact,
            email=technician.email,
            experience_years=technician.experience_years
        )
        db.add(db_technician)
        db.commit()
        db.refresh(db_technician)
        return db_technician
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating technician: {str(e)}")

@app.get("/api/technicians", response_model=List[TechnicianResponse])
async def get_all_technicians(speciality: str = None, db: Session = Depends(get_db)):
    """Get all technicians, optionally filter by speciality"""
    try:
        query = db.query(Technician)
        if speciality:
            query = query.filter(Technician.speciality.ilike(f"%{speciality}%"))
        technicians = query.all()
        return technicians
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching technicians: {str(e)}")

@app.get("/api/technicians/{technician_id}", response_model=TechnicianResponse)
async def get_technician(technician_id: int, db: Session = Depends(get_db)):
    """Get technician by ID"""
    try:
        technician = db.query(Technician).filter(Technician.id == technician_id).first()
        if not technician:
            raise HTTPException(status_code=404, detail="Technician not found")
        return technician
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching technician: {str(e)}")

@app.put("/api/technicians/{technician_id}", response_model=TechnicianResponse)
async def update_technician(technician_id: int, technician: TechnicianCreate, db: Session = Depends(get_db)):
    """Update a technician"""
    try:
        db_technician = db.query(Technician).filter(Technician.id == technician_id).first()
        if not db_technician:
            raise HTTPException(status_code=404, detail="Technician not found")

        db_technician.name = technician.name
        db_technician.speciality = technician.speciality
        db_technician.contact = technician.contact
        db_technician.email = technician.email
        db_technician.experience_years = technician.experience_years

        db.commit()
        db.refresh(db_technician)
        return db_technician
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating technician: {str(e)}")

@app.delete("/api/technicians/{technician_id}")
async def delete_technician(technician_id: int, db: Session = Depends(get_db)):
    """Delete a technician"""
    try:
        technician = db.query(Technician).filter(Technician.id == technician_id).first()
        if not technician:
            raise HTTPException(status_code=404, detail="Technician not found")

        db.delete(technician)
        db.commit()
        return {"message": f"Technician {technician_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting technician: {str(e)}")

# ==================== SALESMAN MANAGEMENT ====================

@app.post("/api/salesmen", response_model=SalesmanResponse)
async def create_salesman(salesman: SalesmanCreate, db: Session = Depends(get_db)):
    """Create a new salesman"""
    try:
        db_salesman = Salesman(
            name=salesman.name,
            speciality=salesman.speciality,
            contact=salesman.contact,
            email=salesman.email
        )
        db.add(db_salesman)
        db.commit()
        db.refresh(db_salesman)
        return db_salesman
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating salesman: {str(e)}")

@app.get("/api/salesmen", response_model=List[SalesmanResponse])
async def get_all_salesmen(speciality: str = None, db: Session = Depends(get_db)):
    """Get all salesmen, optionally filter by speciality"""
    try:
        query = db.query(Salesman)
        if speciality:
            query = query.filter(Salesman.speciality.ilike(f"%{speciality}%"))
        salesmen = query.all()
        return salesmen
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching salesmen: {str(e)}")

@app.get("/api/salesmen/{salesman_id}", response_model=SalesmanResponse)
async def get_salesman(salesman_id: int, db: Session = Depends(get_db)):
    """Get salesman by ID"""
    try:
        salesman = db.query(Salesman).filter(Salesman.id == salesman_id).first()
        if not salesman:
            raise HTTPException(status_code=404, detail="Salesman not found")
        return salesman
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching salesman: {str(e)}")

@app.put("/api/salesmen/{salesman_id}", response_model=SalesmanResponse)
async def update_salesman(salesman_id: int, salesman: SalesmanCreate, db: Session = Depends(get_db)):
    """Update a salesman"""
    try:
        db_salesman = db.query(Salesman).filter(Salesman.id == salesman_id).first()
        if not db_salesman:
            raise HTTPException(status_code=404, detail="Salesman not found")

        db_salesman.name = salesman.name
        db_salesman.speciality = salesman.speciality
        db_salesman.contact = salesman.contact
        db_salesman.email = salesman.email

        db.commit()
        db.refresh(db_salesman)
        return db_salesman
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating salesman: {str(e)}")

@app.delete("/api/salesmen/{salesman_id}")
async def delete_salesman(salesman_id: int, db: Session = Depends(get_db)):
    """Delete a salesman"""
    try:
        salesman = db.query(Salesman).filter(Salesman.id == salesman_id).first()
        if not salesman:
            raise HTTPException(status_code=404, detail="Salesman not found")

        db.delete(salesman)
        db.commit()
        return {"message": f"Salesman {salesman_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting salesman: {str(e)}")

# ==================== EMPLOYEE MANAGEMENT ====================

@app.post("/api/employees", response_model=EmployeeResponse)
async def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    """Create a new employee"""
    try:
        db_employee = Employee(
            name=employee.name,
            position=employee.position,
            department=employee.department,
            contact=employee.contact,
            email=employee.email
        )
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        return db_employee
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating employee: {str(e)}")

@app.get("/api/employees", response_model=List[EmployeeResponse])
async def get_all_employees(department: str = None, db: Session = Depends(get_db)):
    """Get all employees, optionally filter by department"""
    try:
        query = db.query(Employee)
        if department:
            query = query.filter(Employee.department.ilike(f"%{department}%"))
        employees = query.all()
        return employees
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

@app.get("/api/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: int, db: Session = Depends(get_db)):
    """Get employee by ID"""
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        return employee
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employee: {str(e)}")

@app.put("/api/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(employee_id: int, employee: EmployeeCreate, db: Session = Depends(get_db)):
    """Update an employee"""
    try:
        db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not db_employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        db_employee.name = employee.name
        db_employee.position = employee.position
        db_employee.department = employee.department
        db_employee.contact = employee.contact
        db_employee.email = employee.email

        db.commit()
        db.refresh(db_employee)
        return db_employee
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating employee: {str(e)}")

@app.delete("/api/employees/{employee_id}")
async def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """Delete an employee"""
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        db.delete(employee)
        db.commit()
        return {"message": f"Employee {employee_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting employee: {str(e)}")

# ==================== CHAT HISTORY ====================

@app.get("/api/chat-history/{email}")
async def get_chat_history(email: str, db: Session = Depends(get_db)):
    """Get chat history for a specific user"""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

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

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Metro Chatbot",
        "version": "2.0.0",
        "database": "connected"
    }

# ==================== DOCUMENT MANAGEMENT ====================

@app.post("/api/documents/add", response_model=DocumentAddResponse)
async def add_document(document: DocumentAdd):
    """
    Add a document to the Pinecone knowledge base

    Request:
    {
        "text": "Document text to add to knowledge base",
        "metadata": {"source": "manual", "category": "example"}  // optional
    }

    Response:
    {
        "message": "Document added successfully",
        "chunks_processed": 5
    }
    """
    try:
        chunks_count = pinecone_service.add_documents(
            text=document.text,
            metadata=document.metadata
        )

        return {
            "message": "Document added successfully to knowledge base",
            "chunks_processed": chunks_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add document: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8000)),
        reload=True
    )
