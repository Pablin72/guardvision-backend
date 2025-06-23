import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    
    #Conexión a la base de datos postgres

    SQLALCHEMY_DATABASE_URI =  os.getenv("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
