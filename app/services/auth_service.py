from passlib.context import CryptContext

from app.models.helpers import serialize_user, utcnow
from app.utils.errors import AppError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db):
        self.db = db

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def register(self, name: str, email: str, password: str) -> dict:
        existing = await self.db.users.find_one({"email": email.lower()})
        if existing:
            raise AppError("Email already registered", status_code=400)

        doc = {
            "name": name,
            "email": email.lower(),
            "password": self.hash_password(password),
            "created_at": utcnow(),
        }
        result = await self.db.users.insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_user(doc)

    async def login(self, email: str, password: str) -> dict:
        user = await self.db.users.find_one({"email": email.lower()})
        if not user or not self.verify_password(password, user["password"]):
            raise AppError("Invalid email or password", status_code=401)
        return serialize_user(user)

    async def get_user_by_id(self, user_id: str) -> dict | None:
        from bson import ObjectId

        if not ObjectId.is_valid(user_id):
            return None
        user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        return serialize_user(user)
