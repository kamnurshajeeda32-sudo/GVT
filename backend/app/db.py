import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.engine import URL
class Base(DeclarativeBase): pass
def database_url():
    return URL.create("postgresql+psycopg", username="grtalgo_user", password=os.environ["POSTGRES_PASSWORD"], host="postgres", database="grtalgo_db")
def session():
    engine = get_engine()
    with sessionmaker(engine)() as db:
        yield db
from functools import lru_cache
@lru_cache
def get_engine():
    return create_engine(database_url(), pool_size=2, max_overflow=2, pool_pre_ping=True)
