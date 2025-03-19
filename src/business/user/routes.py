from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from core.config import CONFIG

from .models import User
from .schemas import Token, UserCreate, UserSchema
from .service import CurrentUser, authenticate_user, create_access_token, get_password_hash

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me", response_model=UserSchema)
async def get_me(current_user: CurrentUser):
    """Get information about the currently authenticated user."""
    return current_user


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user with email and password."""
    # Check if user with this email already exists
    existing_user = await User.find_one(User.email == user_data.email.lower())
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

    # Create new user with hashed password
    password_hash = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email.lower(),
        password_hash=password_hash,
        photo_url=user_data.photo_url,
    )
    await new_user.insert()
    return new_user


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login, get an access token for future requests."""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(days=CONFIG.SECURITY.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(data={"sub": user.email, "name": user.name}, expires_delta=access_token_expires)

    return Token(access_token=access_token, token_type="bearer")
