from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Numeric
from typing import Optional

Base = declarative_base()

class User(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    email: EmailStr
    balance: Optional[float] = 10.00

class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, index=True)
    password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, index=True)
    balance = Column(Numeric(scale=2))
    account_number = Column(Integer)

class UserLogin(BaseModel):
    username: str
    password: str

class Transfer(BaseModel):
    dest_account: int
    amount: float

class EditUser(BaseModel):
    email: str
    username: str

