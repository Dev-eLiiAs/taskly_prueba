from models.database import Database

class User:
    def __init__(self, user_id=None, username=None, password=None, 
                 email=None, full_name=None, role=None):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.email = email
        self.full_name = full_name
        self.role = role
    
    @staticmethod
    def authenticate(username, password):
        db = Database()
        conn = db.get_connection()
        
        try:
            with conn.cursor() as cursor:
                query = "SELECT * FROM users WHERE username = %s AND password = %s"
                cursor.execute(query, (username, password))
                result = cursor.fetchone()
                
                if result:
                    return User(
                        user_id=result['user_id'],
                        username=result['username'],
                        password=result['password'],
                        email=result['email'],
                        full_name=result['full_name'],
                        role=result['role']
                    )
        except Exception as e:
            print(f"Authentication error: {e}")
        finally:
            db.close_connection()
        
        return None
    
    def save(self):
        db = Database()
        conn = db.get_connection()
        
        try:
            with conn.cursor() as cursor:
                if self.user_id is None:
                    query = """INSERT INTO users (username, password, email, full_name, role) 
                              VALUES (%s, %s, %s, %s, %s)"""
                    cursor.execute(query, (self.username, self.password, 
                                         self.email, self.full_name, self.role))
                    self.user_id = cursor.lastrowid
                else:
                    query = """UPDATE users SET username = %s, password = %s, 
                              email = %s, full_name = %s, role = %s 
                              WHERE user_id = %s"""
                    cursor.execute(query, (self.username, self.password, 
                                         self.email, self.full_name, 
                                         self.role, self.user_id))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Save error: {e}")
            conn.rollback()
            return False
        finally:
            db.close_connection()
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role
        }