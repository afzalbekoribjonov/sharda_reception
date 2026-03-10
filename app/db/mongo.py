from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings


class Mongo:
    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None

    def connect(self) -> None:
        if self._client is not None:
            return
        self._client = AsyncIOMotorClient(settings.MONGO_URI)
        self._db = self._client[settings.MONGO_DB]

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            raise RuntimeError("Mongo is not connected. Call mongo.connect() first.")
        return self._db

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
        self._client = None
        self._db = None


mongo = Mongo()