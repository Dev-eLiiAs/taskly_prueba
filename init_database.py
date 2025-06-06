# init_database.py
import mysql.connector
from mysql.connector import Error
import os
from config import Config

def create_database_and_tables():
    """Crear la base de datos y las tablas si no existen"""
    try:
        print("🔧 Verificando/creando base de datos...")
        
        # Conectar a MySQL sin especificar la base de datos
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Crear la base de datos si no existe
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME}")
            print(f"✅ Base de datos '{Config.DB_NAME}' verificada/creada")
            
            # Usar la base de datos
            cursor.execute(f"USE {Config.DB_NAME}")
            
            # Verificar si las tablas ya existen
            cursor.execute("SHOW TABLES")
            existing_tables = [table[0] for table in cursor.fetchall()]
            
            if not existing_tables:
                print("📋 Creando estructura de tablas...")
                
                # Leer y ejecutar el archivo database.sql
                if os.path.exists('database.sql'):
                    with open('database.sql', 'r', encoding='utf-8') as file:
                        sql_script = file.read()
                    
                    # Dividir el script en declaraciones individuales
                    statements = []
                    current_statement = ""
                    
                    for line in sql_script.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('--'):
                            current_statement += line + " "
                            if line.endswith(';'):
                                statements.append(current_statement.strip())
                                current_statement = ""
                    
                    # Ejecutar cada declaración
                    for statement in statements:
                        if statement.strip():
                            try:
                                cursor.execute(statement)
                            except Error as e:
                                # Ignorar errores de elementos que ya existen
                                if "already exists" not in str(e).lower():
                                    print(f"⚠️  Advertencia ejecutando: {statement[:50]}... - {e}")
                    
                    connection.commit()
                    print("✅ Estructura de base de datos inicialiada")
                else:
                    # Crear tablas manualmente si no existe database.sql
                    print("📋 Archivo database.sql no encontrado, creando tablas manualmente...")
                    create_tables_manually(cursor, connection)
            else:
                print(f"ℹ️  Tablas existentes encontradas: {', '.join(existing_tables)}")
            
            return True
            
    except Error as e:
        print(f"❌ Error de MySQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def create_tables_manually(cursor, connection):
    """Crear tablas manualmente si no existe database.sql"""
    try:
        # Tabla users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                role ENUM('Organizador', 'Participante') DEFAULT 'Participante',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla tasks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                due_date DATE,
                priority ENUM('high', 'medium', 'low') DEFAULT 'medium',
                status ENUM('pending', 'in_progress', 'completed') DEFAULT 'pending',
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Tabla events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                event_date DATETIME NOT NULL,
                location VARCHAR(255),
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Datos de prueba
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            print("👥 Creando usuarios de prueba...")
            cursor.execute("""
                INSERT INTO users (username, password, email, full_name, role) VALUES
                ('admin', 'admin123', 'admin@taskly.com', 'Administrador', 'Organizador'),
                ('user1', 'user123', 'user1@taskly.com', 'Usuario Test', 'Participante')
            """)
        
        connection.commit()
        print("✅ Tablas creadas manualmente")
        
    except Error as e:
        print(f"❌ Error creando tablas: {e}")
        raise

def verify_database_connection():
    """Verificar que se puede conectar a la base de datos"""
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        
        if connection.is_connected():
            connection.close()
            return True
        return False
        
    except Error:
        return False

if __name__ == "__main__":
    create_database_and_tables()