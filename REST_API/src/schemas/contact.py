from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field



class ContactSchema(BaseModel):
    first_name: str = Field(min_length=3, max_length=50)
    last_name: str 
    email: EmailStr
    phone_number: str = Field(pattern=r"^\+\d{12}$")
    birthday: date 
    extra_data: Optional[str]

class ContactResponse(ContactSchema):
    id: int = 1
    created_at: datetime | None
    updated_at: datetime | None   
    
    class Config:
        from_attributes = True