from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr
from business.user.schemas import UserSchema

class AddFriendResponse(BaseModel):
    id: str
    requester_id:str
    recipient_id:str
    status:str
    created_at: datetime


    model_config = {"from_attributes": True}
    
