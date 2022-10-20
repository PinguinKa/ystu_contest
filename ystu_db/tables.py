from sqlalchemy import Column, Integer, String
from .db import Base


class Users(Base):

    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True,  unique=True)
    last_name = Column(String)
    first_name = Column(String)
    middle_name = Column(String)
    university = Column(String)
    login = Column(String, unique=True, primary_key=True)
    password = Column(String)


class Items(Base):

    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, index=True,  unique=True)
    name = Column(String)
    description = Column(String)
    image = Column(String)
    price = Column(Integer)



