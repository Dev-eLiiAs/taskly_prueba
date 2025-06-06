import os

class Config:
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-taskly'
    
    # Database configuration
    DB_HOST = 'localhost'
    DB_PORT = '3306'
    DB_NAME = 'taskly'
    DB_USER = 'root'
    DB_PASSWORD  = 'admin'
    
    # App configuration
    DEBUG = True