from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository


class EmailAlreadyExists(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def register(self, email: str, password: str) -> User:
        if await self.users.get_by_email(email):
            raise EmailAlreadyExists(email)
        return await self.users.create(email=email, hashed_password=hash_password(password))

    async def authenticate(self, email: str, password: str) -> str:
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentials()
        if not user.is_active:
            raise InvalidCredentials()
        return create_access_token(subject=str(user.id))
