from datetime import datetime
from typing import List

from pydantic import BaseModel


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
