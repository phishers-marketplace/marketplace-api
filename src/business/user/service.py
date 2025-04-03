import logging
import secrets
import random, string
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Optional
import os
# import rsa 
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
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

def generate_rsa_keys():
    """Generates an RSA key pair"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    # public_key = private_key.public_key()
    public_key = private_key.public_key()
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()  # ✅ Convert bytes to a string
    return private_key, public_key, public_key_pem

# def encrypt_private_key(private_key, password):
#     """Encrypts a private key with a user-defined password"""
#     salt = os.urandom(16)  # Generate a random salt
#     # salt= ''.join([random.choice(string.digits + string.ascii_letters) for _ in range(16)]) 
#     # print('plain salt is ',salt)
#     # print('encoded salt is',base64.b64encode(salt))
#     # print('str and encoded salt is',base64.b64encode(salt).decode('utf-8'))
#     # print('decoded encoded salt is',base64.b64decode(base64.b64encode(salt).decode('utf-8')))
#     # Derive a strong encryption key from password + salt
#     kdf = PBKDF2HMAC(
#         algorithm=hashes.SHA256(),
#         length=32,  # 32-byte key for AES
#         salt=salt,
#         iterations=100000
#     )
#     derived_key = kdf.derive(password.encode())  # This is the actual encryption key

#     # Encrypt the private key using the derived key
#     encrypted_private_key = private_key.private_bytes(
#         encoding=serialization.Encoding.PEM,
#         format=serialization.PrivateFormat.PKCS8,
#         encryption_algorithm=serialization.BestAvailableEncryption(derived_key)  # ✅ Fix: Use raw derived_key
#     )

#     # Convert private key to Base64 before storing (safe for DB storage)
#     encrypted_private_key_b64 = base64.b64encode(encrypted_private_key).decode()

#     # Convert public key to PEM format
#     public_key = private_key.public_key()
#     public_pem = public_key.public_bytes(
#         encoding=serialization.Encoding.PEM,
#         format=serialization.PublicFormat.SubjectPublicKeyInfo
#     ).decode()  # ✅ Convert bytes to a string

#     return base64.b64encode(salt).decode(), encrypted_private_key_b64, public_pem
    # return salt, encrypted_private_key, public_pem
def encrypt_private_key(private_key, password):
    """Encrypt an RSA private key using only a password (AES-256-CBC)"""
    
    # Generate random salt (16 bytes)
    salt = os.urandom(16)
    
    # Derive a 32-byte AES key from password + salt using PBKDF2
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 32-byte (256-bit) key for AES-256
        salt=salt,
        iterations=100000
    )
    aes_key = kdf.derive(password.encode())

    # Generate random IV (Initialization Vector, 16 bytes)
    iv = os.urandom(16)

    # Convert private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Encrypt using AES-256-CBC
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()

    # PKCS7 Padding (AES requires input in multiples of 16 bytes)
    pad_len = 16 - (len(private_pem) % 16)
    padded_private_pem = private_pem + bytes([pad_len] * pad_len)

    encrypted_private_key = encryptor.update(padded_private_pem) + encryptor.finalize()

    # Encode everything in Base64 for safe storage
    return base64.b64encode(encrypted_private_key).decode(),base64.b64encode(salt).decode(),base64.b64encode(iv).decode()

def decrypt_private_key(encrypted_private_key_b64, salt_b64, password):
    """Decrypts the encrypted private key using the user-provided password"""

    # Decode Base64-encoded salt and encrypted private key
    salt = base64.b64decode(salt_b64)
    encrypted_private_key = base64.b64decode(encrypted_private_key_b64)

    # Derive the encryption key using the same KDF method
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 32-byte key for AES
        salt=salt,
        iterations=100000
    )
    derived_key = kdf.derive(password.encode())  # Must match the encryption key

    # Load and decrypt the private key
    private_key = serialization.load_pem_private_key(
        encrypted_private_key,
        password=derived_key,
    )

    return private_key  # Returns the private key object

# Create CurrentUser dependency for routes
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[CurrentUser, Depends(get_admin_user)]


