import os

class Config:
    
    SECRET_KEY =   'dev-secret-key-taskly'
    
    # Database configuration
    DB_HOST = 'localhost'
    DB_PORT = '3306'
    DB_NAME = 'taskly'
    DB_USER = 'root'
    DB_PASSWORD  = '123'
    
    # App configuration
    DEBUG = True