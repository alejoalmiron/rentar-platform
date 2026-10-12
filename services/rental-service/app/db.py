import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

dotenv_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(dotenv_path=dotenv_path, override=True)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:root@localhost:3307/rental_db")

if DATABASE_URL:
    if "mysql://" in DATABASE_URL and "mysql+pymysql://" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
    elif "mysql+mysqldb://" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("mysql+mysqldb://", "mysql+pymysql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()