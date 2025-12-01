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
    Register a new user with email verification
    
    - Developer and Public Viewer are auto-approved
    - Others need approval from their admin
    - All users must verify their email
    """
    from backend.utils.email_validator import validate_email
    from backend.utils.email_service import send_verification_email
    import secrets
    
    # Validate role
    if request.role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {ALL_ROLES}")
    
    # Validate email format and domain
    is_valid, error_message = validate_email(request.email, request.role)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
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
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    token_expires = datetime.utcnow() + timedelta(hours=24)
    
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
        approved=approved,
        email_verified=False,
        verification_token=verification_token,
        verification_token_expires=token_expires
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send verification email
    try:
        send_verification_email(user.email, user.name, verification_token)
    except Exception as e:
        # Log error but don't fail registration
        print(f"Failed to send verification email: {str(e)}")
    
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
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email address before logging in. Check your inbox for the verification link."
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


@ro
uter.get("/verify-email/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Verify user email with token
    
    Args:
        token: Verification token from email link
    
    Returns:
        Success message and user info
    """
    from backend.utils.email_service import send_verification_success_email
    
    # Find user by token
    user = db.query(User).filter(User.verification_token == token).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Invalid verification token")
    
    # Check if already verified
    if user.email_verified:
        return {
            "status": "already_verified",
            "message": "Email already verified",
            "user": {
                "name": user.name,
                "email": user.email
            }
        }
    
    # Check if token expired
    if user.verification_token_expires and user.verification_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Verification token has expired. Please request a new one."
        )
    
    # Verify email
    user.email_verified = True
    user.verification_token = None  # Clear token after use
    user.verification_token_expires = None
    db.commit()
    
    # Send success email
    try:
        send_verification_success_email(user.email, user.name)
    except Exception as e:
        print(f"Failed to send success email: {str(e)}")
    
    # Log verification
    audit = AuditLog(
        user_id=user.id,
        action="email_verified",
        action_metadata={"email": user.email}
    )
    db.add(audit)
    db.commit()
    
    return {
        "status": "success",
        "message": "Email verified successfully! Your account is now pending admin approval.",
        "user": {
            "name": user.name,
            "email": user.email,
            "approved": user.approved
        }
    }


@router.post("/resend-verification")
async def resend_verification(email: EmailStr, db: Session = Depends(get_db)):
    """
    Resend verification email
    
    Args:
        email: User's email address
    
    Returns:
        Success message
    """
    from backend.utils.email_service import send_verification_email
    import secrets
    
    # Find user
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Don't reveal if email exists or not
        return {
            "status": "success",
            "message": "If the email exists, a verification link has been sent."
        }
    
    # Check if already verified
    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Generate new token
    verification_token = secrets.token_urlsafe(32)
    token_expires = datetime.utcnow() + timedelta(hours=24)
    
    user.verification_token = verification_token
    user.verification_token_expires = token_expires
    db.commit()
    
    # Send email
    try:
        send_verification_email(user.email, user.name, verification_token)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to send verification email. Please try again later."
        )
    
    return {
        "status": "success",
        "message": "Verification email sent successfully. Please check your inbox."
    }
