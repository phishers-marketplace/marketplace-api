from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr
from business.user.schemas import UserSchema

class GroupSchema(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime | None = None
    created_by: str
    # members: List[UserSchema] = []

    model_config = {"from_attributes": True}
    
    
class GroupsListResponse(BaseModel):
    groups_list: List[GroupSchema]