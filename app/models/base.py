from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
 
class BaseModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    # created_at: datetime = Field(default_factory=datetime.utcnow)
    # updated_at: datetime = Field(default_factory=datetime.utcnow) 
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) 