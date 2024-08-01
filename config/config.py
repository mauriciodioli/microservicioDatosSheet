from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # Cargar variables de entorno desde el archivo .env
    MYSQL_USER = os.environ.get("MYSQL_USER")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
    MYSQL_HOST = os.environ.get("MYSQL_HOST")
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE")
    MYSQL_PORT = os.environ.get("MYSQL_PORT", "3307")  # Default to 3306 if MYSQL_PORT is not set

    # Configuración de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
