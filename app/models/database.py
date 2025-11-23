import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv(override=True)


class Database:
    def __init__(self):
        self.database_url = f"mysql+pymysql://{os.environ.get('MYSQL_USER')}:{os.environ.get('MYSQL_PASSWORD')}@{os.environ.get('MYSQL_HOST')}:{os.environ.get('MYSQL_PORT')}/{os.environ.get('MYSQL_DB')}"

        self.engine = create_engine(
            self.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = declarative_base()

    def get_session(self):
        session = self.SessionLocal()
        try:
            return session
        finally:
            session.close()

    def create_tables(self):
        self.Base.metadata.create_all(bind=self.engine)


db = Database()
Base = db.Base


def get_db():
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()