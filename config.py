"""
I use this file to manage all the 'hidden' settings for my Flask app. 
It basically tells my code how to find the database and how to stay secure, 
whether I am working on my own laptop (local) or putting it online (Render).
"""

import os
# I use this to pull variables from my hidden .env file into the script
from dotenv import load_dotenv

# I run this at the start so the app knows where to look for my secrets
load_dotenv()

class Config:
    """Stores Flask and database configuration values."""
    
    # I use this key to keep my web sessions and forms secure.
    # If I am on Render, it grabs my real key; otherwise, it uses a dummy one for dev.
    SECRET_KEY = os.getenv("SECRET_KEY", "development-secret-key")
    
    # This is the address for my database. 
    # Locally, I use a simple SQLite file, but on Render, it points to my Postgres DB.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///portfolio_database.db")
    
    # I set this to False to stop SQLAlchemy from tracking every tiny change. 
    # It keeps the app running faster and uses less memory.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # This is a critical fix for deployment! 
    # Render often provides a URL starting with 'postgres://', but SQLAlchemy 
    # needs 'postgresql://' to work. I check for that here and swap it if needed.
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)