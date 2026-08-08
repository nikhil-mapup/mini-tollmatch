from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class InvalidRecord(BaseModel, Generic[T]):
    record: T
    errors: list[str]

class ValidationResult(BaseModel, Generic[T]):
    valid_records: list[T]
    invalid_records: list[InvalidRecord[T]]