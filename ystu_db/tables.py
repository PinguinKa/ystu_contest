from sqlalchemy import Column
from sqlalchemy.types import Integer, String, LargeBinary, Float
from .db import Base


class Users(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True, unique=True)
    last_name = Column(String)
    first_name = Column(String)
    middle_name = Column(String)
    university = Column(String)
    login = Column(String, unique=True, primary_key=True)
    password = Column(String)
    participation = Column(String)


class Events(Base):

    __tablename__ = 'events'

    id = Column(Integer, index=True, unique=True)
    name = Column(String, unique=True, primary_key=True)
    begin_date = Column(String)
    exp_date = Column(String)
    start = Column(String)
    end = Column(String)
    title = Column(String)
    subtitle = Column(String)
    info = Column(String)
    themes = Column(String)



class Submits(Base):

    __tablename__ = 'submits'

    id = Column(Integer, primary_key=True, index=True, unique=True)
    login = Column(String, primary_key=True)
    filename = Column(String)
    file = Column(LargeBinary)
    event = Column(String)
    theme = Column(String)
    scientific_director = Column(String)
    num_of_checks = Column(Integer)
    jury_members = Column(String)



class Reviews(Base):

    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, unique=True)
    jury = Column(String, primary_key=True)
    criteria1 = Column(Integer)
    criteria2 = Column(Integer)
    criteria3 = Column(Integer)
    criteria4 = Column(Integer)
    sum = Column(Integer)



class Rating(Base):

    __tablename__ = 'rating'

    login = Column(String, primary_key=True)
    last_name = Column(String)
    first_name = Column(String)
    middle_name = Column(String)
    submit_id = Column(Integer, primary_key=True, unique=True)
    link = Column(String)
    university = Column(String)
    event = Column(String)
    theme = Column(String)
    scientific_director = Column(String)
    final_score = Column(Float)