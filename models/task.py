from models.database import Database
from datetime import datetime, date

class Task:
    def __init__(self, task_id=None, title=None, description=None, 
                 due_date=None, priority='medium', status='pending', 
                 user_id=None, created_at=None):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.priority = priority
        self.status = status
        self.user_id = user_id
        self.created_at = created_at
    
    @staticmethod
    def get_by_user(user_id):
        db = Database()
        conn = db.get_connection()
        tasks = []
        
        try:
            with conn.cursor() as cursor:
                query = """SELECT * FROM tasks WHERE user_id = %s 
                          ORDER BY 
                          CASE priority 
                            WHEN 'high' THEN 1 
                            WHEN 'medium' THEN 2 
                            WHEN 'low' THEN 3 
                          END,
                          due_date ASC"""
                cursor.execute(query, (user_id,))
                results = cursor.fetchall()
                
                for row in results:
                    tasks.append(Task(
                        task_id=row['task_id'],
                        title=row['title'],
                        description=row['description'],
                        due_date=row['due_date'],
                        priority=row['priority'],
                        status=row['status'],
                        user_id=row['user_id'],
                        created_at=row['created_at']
                    ))
        except Exception as e:
            print(f"Error fetching tasks: {e}")
        finally:
            db.close_connection()
        
        return tasks
    
    @staticmethod
    def get_by_id(task_id):
        db = Database()
        conn = db.get_connection()
        
        try:
            with conn.cursor() as cursor:
                query = "SELECT * FROM tasks WHERE task_id = %s"
                cursor.execute(query, (task_id,))
                result = cursor.fetchone()
                
                if result:
                    return Task(
                        task_id=result['task_id'],
                        title=result['title'],
                        description=result['description'],
                        due_date=result['due_date'],
                        priority=result['priority'],
                        status=result['status'],
                        user_id=result['user_id'],
                        created_at=result['created_at']
                    )
        except Exception as e:
            print(f"Error fetching task: {e}")
        finally:
            db.close_connection()
        
        return None
    
    def save(self):
        db = Database()
        conn = db.get_connection()
        
        try:
            with conn.cursor() as cursor:
                if self.task_id is None:
                    query = """INSERT INTO tasks (title, description, due_date, 
                              priority, status, user_id) 
                              VALUES (%s, %s, %s, %s, %s, %s)"""
                    cursor.execute(query, (self.title, self.description, 
                                         self.due_date, self.priority, 
                                         self.status, self.user_id))
                    self.task_id = cursor.lastrowid
                else:
                    query = """UPDATE tasks SET title = %s, description = %s, 
                              due_date = %s, priority = %s, status = %s 
                              WHERE task_id = %s"""
                    cursor.execute(query, (self.title, self.description, 
                                         self.due_date, self.priority, 
                                         self.status, self.task_id))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Task save error: {e}")
            conn.rollback()
            return False
        finally:
            db.close_connection()
    
    def delete(self):
        db = Database()
        conn = db.get_connection()
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM tasks WHERE task_id = %s", (self.task_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Task delete error: {e}")
            return False
        finally:
            db.close_connection()
    
    def get_priority_color(self):
        colors = {
            'high': 'danger',
            'medium': 'warning', 
            'low': 'success'
        }
        return colors.get(self.priority, 'secondary')
    
    def is_urgent(self):
        if self.due_date:
            days_left = (self.due_date - date.today()).days
            return days_left <= 3
        return False
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            'priority': self.priority,
            'status': self.status,
            'user_id': self.user_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'color_class': self.get_priority_color(),
            'is_urgent': self.is_urgent()
        }