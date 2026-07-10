from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List

security = HTTPBearer()

class UserMock:
    id = 1
    email = "farmer@agrolink.ai"
    role = "FARMER"

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    return UserMock()

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: UserMock = Security(get_current_user)):
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )
        return current_user