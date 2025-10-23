import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'your_username'),
    'password': os.getenv('DB_PASSWORD', 'your_password'),
    'database': os.getenv('DB_NAME', 'dag_generator'),
    'charset': 'utf8mb4'
}

# Flask configuration
class Config:
    # SECRET_KEY is not required for this server-only setup; keep None
    SECRET_KEY = None
    # Default DEBUG to False in server environments unless explicitly set
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def get_db_connection():
    """Return a new pymysql connection using DB_CONFIG."""
    try:
        import pymysql
    except Exception:
        raise RuntimeError('pymysql is required for DB connections. Install with pip install pymysql')

    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset=DB_CONFIG.get('charset', 'utf8mb4')
    )