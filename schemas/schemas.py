from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "student"   # ← Ye add kar do

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CourseBase(BaseModel):
    title: str
    description: str
    thumbnail: Optional[str] = None

class CourseResponse(CourseBase):
    id: int
    instructor_id: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    name: str = ""
    role: str = ""
    email: str = ""