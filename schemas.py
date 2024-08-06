from pydantic import BaseModel, EmailStr
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class RegisterUser(BaseModel):
    email: EmailStr
    password: str
    message: str


class Question(BaseModel):
    user_id: str
    question: str


class UserResponse(BaseModel):
    id: int
    email: str
    tokens: int

    class Config:
        orm_mode = True
