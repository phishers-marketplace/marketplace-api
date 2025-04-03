from fastapi import APIRouter

from business.groups.models import Group, GroupMembership
from business.groups.schemas import GroupsListResponse
from business.user.service import CurrentUser

router = APIRouter(prefix="/groups", tags=["user"])


@router.get("/", response_model=GroupsListResponse)
async def get_groups(current_user: CurrentUser):
    # get all group_id objects where the user is a member
    groups = await GroupMembership.distinct("user_id", {"user_id": current_user.id})
    print("groups:", groups)
    groups_list = []

    # find all group objects where user is a member
    for group in groups:
        groups_list.append(Group.find_one(Group.id == group.id))
    return GroupsListResponse(groups_list=groups_list)
