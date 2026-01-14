# core/base_repository.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from tortoise.models import Model
from pydantic import BaseModel

T = TypeVar("T", bound=Model)
S = TypeVar("S", bound=BaseModel)

class BaseRepository(Generic[T, S]):
    def __init__(self, model: Type[T], response_schema: Type[S]):
        self.model = model
        self.response_schema = response_schema
    
    async def get_by_id(self, id: str) -> Optional[T]:
        return await self.model.get_or_none(id=id)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        return await self.model.all().offset(skip).limit(limit)
    
    async def create(self, payload: Dict[str, Any]) -> T:
        return await self.model.create(**payload)
    
    async def update(self, obj: T, data: Dict[str, Any]) -> T:
        update_data = {k: v for k, v in data.items() if v is not None}
        for key, value in update_data.items():
            setattr(obj, key, value)
        await obj.save()
        return obj
    
    async def delete(self, obj: T) -> bool:
        await obj.delete()
        return True
    
    async def to_schema(self, obj: T) -> S:
        """Convert model instance to response schema"""
        return self.response_schema.model_validate(obj.__dict__)