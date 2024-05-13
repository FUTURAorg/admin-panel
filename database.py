import os
from databases import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table

DATABASE_URL = os.environ.get("DB_URL")

database = Database(DATABASE_URL)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Reflect each table you need from the existing database
class User(Base):
    __table__ = Table('users', MetaData(), autoload_with=engine)
