from typing import Optional, List
from pydantic import BaseModel

class OperatorCreate(BaseModel):
    name: str
    max_load: int = 10

class OperatorRead(OperatorCreate):
    id: int
    is_active: bool
    class Config:
        from_attributes = True

class SourceCreate(BaseModel):
    name: str

class SourceConfigUpdate(BaseModel):
    operator_id: int
    weight: int

class InteractionCreate(BaseModel):
    external_lead_id: str
    source_id: int
    message: Optional[str] = None

class InteractionRead(BaseModel):
    id: int
    lead_id: int
    operator_id: Optional[int]
    status: str