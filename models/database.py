import pymysql
from config import Config

class Database:
    def __init__(self):
        self.connection = None
    
    def get_connection(self):
        try:
            if self.connection is None or not self.connection.open:
                self.connection = pymysql.connect(
                    host=Config.DB_HOST,
                    port=int(Config.DB_PORT),
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME,
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
        except Exception as e:
            print(f"Error connecting to database: {e}")
            
        return self.connection
    
    def close_connection(self):
        if self.connection and self.connection.open:
            self.connection.close()