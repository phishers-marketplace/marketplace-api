import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import EmailStr

from core.config import CONFIG

from .models import User
from .schemas import Token, TokenData

logger = logging.getLogger("uvicorn")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.

    For password_hash stored in format: <salt>:<hash>
    """
    if ":" not in hashed_password:
        return False

    stored_salt, stored_hash = hashed_password.split(":", 1)
    password_to_check = f"{plain_password}{stored_salt}"
    return pwd_context.verify(password_to_check, stored_hash)


def get_password_hash(password: str) -> str:
    """Hash a password for storing.

    Returns string in format: <salt>:<hash> for added security.
    """
    # Generate a random salt
    salt = secrets.token_hex(16)
    # Hash the password with the salt
    salted_password = f"{password}{salt}"
    hashed_password = pwd_context.hash(salted_password)
    # Return salt and hash together
    return f"{salt}:{hashed_password}"


async def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password."""
    try:
        user = await User.find_one(User.email == email.lower())

        if not user:
            logger.warning(f"Authentication attempt for non-existent user: {email}")
            return None

        if not verify_password(password, user.password_hash):
            logger.warning(f"Failed authentication attempt for user: {email}")
            return None

        return user

    except Exception as e:
        logger.exception(f"Error during authentication: {str(e)}")
        return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token with the provided data."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)

    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})

    return jwt.encode(to_encode, CONFIG.SECURITY.JWT_SECRET_KEY, algorithm="HS256")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current user from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, CONFIG.SECURITY.JWT_SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")

        if email is None:
            raise credentials_exception

        token_data = TokenData(email=email)
    except InvalidTokenError as e:
        logger.error(f"Token validation error: {str(e)}")
        raise credentials_exception

    user = await User.find_one(User.email == token_data.email)

    if user is None:
        logger.warning(f"User from token not found: {token_data.email}")
        raise credentials_exception

    if user.is_suspended:
        suspension_message = (
            f"Account suspended. Reason: {user.suspension_reason}" if user.suspension_reason else "Account suspended."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=suspension_message,
        )

    return user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Check if the current user has admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required.",
        )
    return current_user


# Create CurrentUser dependency for routes
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_admin_user)]
