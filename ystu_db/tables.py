from sqlalchemy import Column
from sqlalchemy.types import Integer, String, LargeBinary
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


class Submit(Base):

    __tablename__ = 'submit'

    id = Column(Integer, primary_key=True, index=True,  unique=True)
    theme = Column(String)
    filename = Column(String)
    file = Column(LargeBinary)



