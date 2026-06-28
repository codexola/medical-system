import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import AdminUser, Subscription, SubscriptionPlan, SubscriptionStatus, User

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    async def get_or_create_line_user(self, line_user_id: str, name: Optional[str] = None) -> User:
        result = await self.db.execute(select(User).where(User.line_user_id == line_user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(line_user_id=line_user_id, name=name, preferred_language="ja")
            self.db.add(user)
            await self.db.flush()
            await self.create_trial_subscription(user.id)
        return user

    async def create_trial_subscription(self, user_id: uuid.UUID) -> Subscription:
        now = datetime.now(timezone.utc)
        sub = Subscription(
            user_id=user_id,
            plan=SubscriptionPlan.FREE_TRIAL,
            status=SubscriptionStatus.TRIAL,
            trial_start=now,
            trial_end=now + timedelta(days=settings.FREE_TRIAL_DAYS),
        )
        self.db.add(sub)
        await self.db.flush()
        return sub

    def create_access_token(self, user_id: str, role: str = "patient") -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        payload = {"sub": user_id, "role": role, "exp": expire}
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except JWTError:
            return None

    async def authenticate_admin(self, email: str, password: str) -> Optional[AdminUser]:
        result = await self.db.execute(
            select(AdminUser).where(AdminUser.email == email, AdminUser.is_active == True)
        )
        user = result.scalar_one_or_none()
        if not user or not self.verify_password(password, user.password_hash):
            return None
        user.last_login = datetime.now(timezone.utc)
        await self.db.flush()
        return user

    async def register_patient(
        self,
        email: str,
        password: str,
        name: str,
        home_address: str,
        job_function: str,
        phone: Optional[str] = None,
    ) -> User:
        from app.services.google_maps import GoogleMapsService

        latitude, longitude = None, None
        formatted_address = home_address
        geo = await GoogleMapsService().geocode(home_address)
        if geo:
            latitude = geo["latitude"]
            longitude = geo["longitude"]
            formatted_address = geo["formatted_address"]

        user = User(
            email=email,
            password_hash=self.hash_password(password),
            name=name,
            phone=phone,
            address=formatted_address,
            job_function=job_function,
            latitude=latitude,
            longitude=longitude,
            preferred_language="ja",
        )
        self.db.add(user)
        await self.db.flush()
        await self.create_trial_subscription(user.id)
        return user
