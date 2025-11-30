"""Authentication router - handles user registration, login, and JWT tokens"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import bcrypt
import jwt
import os

from backend.database import get_db, User, AuditLog
from backend.constants.roles import ALL_ROLES, DEVELOPER, PUBLIC_VIEWER

router = APIRouter()
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    institution_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    institution_id: Optional[int]
    approved: bool
    created_at: datetime


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user
    
    - Developer and Public Viewer are auto-approved
    - Others need approval from their admin
    """
    # Validate role
    if request.role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {ALL_ROLES}")
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate institution requirement
    roles_needing_institution = ["student", "document_officer", "university_admin"]
    if request.role in roles_needing_institution and not request.institution_id:
        raise HTTPException(status_code=400, detail=f"Institution ID required for {request.role}")
    
    # Hash password
    hashed_password = hash_password(request.password)
    
    # Auto-approve for developer and public_viewer
    auto_approved_roles = [DEVELOPER, PUBLIC_VIEWER]
    approved = request.role in auto_approved_roles
    
    # Create user
    user = User(
        name=request.name,
        email=request.email,
        password_hash=hashed_password,
        role=request.role,
        institution_id=request.institution_id,
        approved=approved
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login user and return JWT token
    """
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # ✅ Change: Return 404 with a specific message
        raise HTTPException(
            status_code=404, 
            detail="User not registered. Please sign up first."
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        # ✅ Change: Specific message for password
        raise HTTPException(
            status_code=401, 
            detail="Incorrect password. Please try again."
        )
    
    # Check if approved
    # if not user.approved:
    #     raise HTTPException(
    #         status_code=403,
    #         detail="Your account is pending approval. Please wait for an admin to approve your registration."
    #     )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "institution_id": user.institution_id,
            "approved": user.approved
        }
    )
    
    # Log login
    audit = AuditLog(
        user_id=user.id,
        action="login",
        action_metadata={"email": user.email}  # ✅ Changed from 'metadata'
    )
    db.add(audit)
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "institution_id": user.institution_id,
            "approved": user.approved
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logout user (client should delete token)"""
    # Log logout
    audit = AuditLog(
        user_id=current_user.id,
        action="logout",
        action_metadata={"email": current_user.email}  # ✅ Changed from 'metadata'
    )
    db.add(audit)
    db.commit()
    
    return {"message": "Successfully logged out"}