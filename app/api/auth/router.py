from fastapi import APIRouter, Depends

from app.api.deps import get_db, get_user_or_404
from app.schemas import UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(payload: UserCreate, db=Depends(get_db)):
    service = AuthService(db)
    return await service.register(payload.name, payload.email, payload.password)


@router.post("/login", response_model=UserResponse)
async def login(payload: UserLogin, db=Depends(get_db)):
    service = AuthService(db)
    return await service.login(payload.email, payload.password)


@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user=Depends(get_user_or_404)):
    return user
