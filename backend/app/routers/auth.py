from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import wajib_auth
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(db, body.email, body.password, body.org_name)
    token = auth_service.create_token(str(user.id), user.email, user.org_name)
    return TokenResponse(
        access_token=token,
        user=UserOut(id=str(user.id), email=user.email, org_name=user.org_name),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.login_user(db, body.email, body.password)
    token = auth_service.create_token(str(user.id), user.email, user.org_name)
    return TokenResponse(
        access_token=token,
        user=UserOut(id=str(user.id), email=user.email, org_name=user.org_name),
    )


@router.get("/me", response_model=UserOut)
async def me(payload: dict = Depends(wajib_auth)):
    return UserOut(id=payload["sub"], email=payload["email"], org_name=payload.get("org_name"))
