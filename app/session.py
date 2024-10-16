import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class SessionConfig():
    def __init__(self):
        ...

    def url(self):
        try:
            db_user = 'postgres'
            db_pass = 'postgres'
            db_host = 'localhost'
            db_name = 'postgres'
            return f'postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}'
        except KeyError as k:
            print(f'No database environment variables found, using SQLite as fallback ({k})')
            return 'sqlite:///./test.db'

session_config = SessionConfig()
engine = create_engine(session_config.url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()