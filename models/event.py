from models.database import Database
from datetime import datetime

class Event:
    def __init__(self, event_id=None, title=None, description=None, 
                 event_date=None, location=None, user_id=None, created_at=None):
        self.event_id = event_id
        self.title = title
        self.description = description
        self.event_date = event_date
        self.location = location
        self.user_id = user_id
        self.created_at = created_at
    
    @staticmethod
    def get_by_user(user_id):
        db = Database()
        conn = db.get_connection()
        events = []
        
        try:
            with conn.cursor() as cursor:
                query = """SELECT * FROM events WHERE user_id = %s 
                          ORDER BY event_date ASC"""
                cursor.execute(query, (user_id,))
                results = cursor.fetchall()
                
                for row in results:
                    events.append(Event(
                        event_id=row['event_id'],
                        title=row['title'],
                        description=row['description'],
                        event_date=row['event_date'],
                        location=row['location'],
                        user_id=row['user_id'],
                        created_at=row['created_at']
                    ))
        except Exception as e:
            print(f"Error fetching events: {e}")
        finally:
            db.close_connection()
        
        return events
    
    @staticmethod
    def get_by_id(event_id):
        db = Database()
        conn = db.get_connection()
        
        try:
            with conn.cursor() as cursor:
                query = "SELECT * FROM events WHERE event_id = %s"
                cursor.execute(query, (event_id,))
                result = cursor.fetchone()
                
                if result:
                    return Event(
                        event_id=result['event_id'],
                        title=result['title'],
                        description=result['description'],
                        event_date=result['event_date'],
                        location=result['location'],
                        user_id=result['user_id'],
                        created_at=result['created_at']
                    )
        except Exception as e:
            print(f"Error fetching event: {e}")
        finally:
            db.close_connection()
        
        return None
    
    def save(self):
        db = Database()
        conn = db.get_connection()
        
        try:
            with conn.cursor() as cursor:
                if self.event_id is None:
                    query = """INSERT INTO events (title, description, event_date, 
                              location, user_id) VALUES (%s, %s, %s, %s, %s)"""
                    cursor.execute(query, (self.title, self.description, 
                                         self.event_date, self.location, self.user_id))
                    self.event_id = cursor.lastrowid
                else:
                    query = """UPDATE events SET title = %s, description = %s, 
                              event_date = %s, location = %s WHERE event_id = %s"""
                    cursor.execute(query, (self.title, self.description, 
                                         self.event_date, self.location, self.event_id))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Event save error: {e}")
            conn.rollback()
            return False
        finally:
            db.close_connection()
    
    def delete(self):
        db = Database()
        conn = db.get_connection()
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM events WHERE event_id = %s", (self.event_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Event delete error: {e}")
            return False
        finally:
            db.close_connection()
    
    def to_dict(self):
        return {
            'event_id': self.event_id,
            'title': self.title,
            'description': self.description,
            'event_date': self.event_date.strftime('%Y-%m-%d %H:%M') if self.event_date else None,
            'location': self.location,
            'user_id': self.user_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }