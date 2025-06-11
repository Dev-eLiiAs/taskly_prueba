from flask import Flask, render_template, session, redirect, url_for, flash
import os
from datetime import datetime
from jinja2.exceptions import TemplateNotFound
from importlib.metadata import version

# Importar configuración
from config import Config

# Importar modelos
from models.database import Database
from models.user import User
from models.task import Task
from models.event import Event

# Importar rutas
from routes.auth import auth_bp
from routes.main import main_bp
from routes.tasks import tasks_bp
from routes.events import events_bp

# Importar inicialización de base de datos
from init_database import create_database_and_tables, verify_database_connection

# ===== CREAR APLICACIÓN FLASK =====
def create_app():
    app = Flask(__name__)

    # Configuración
    app.config.from_object(Config)

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(events_bp)

    # Configurar sesiones
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'taskly:'

    # Seguridad para producción
    if not app.debug:
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['CONTENT_SECURITY_POLICY'] = {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com",
            'style-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            'font-src': "'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com",
            'img-src': "'self' data: https:",
            'connect-src': "'self'"
        }

    return app

# Crear instancia global
app = create_app()

# ===== COMANDO CLI PARA INICIALIZAR BASE DE DATOS =====
@app.cli.command("init-db")
def init_db_command():
    """Inicializa la base de datos y crea las tablas necesarias."""
    try:
        print("🔧 Inicializando base de datos...")
        if create_database_and_tables():
            print("✅ Base de datos inicializada correctamente")
        else:
            print("❌ No se pudo inicializar la base de datos")
    except Exception as e:
        print(f"❌ Error: {e}")

# ===== PUNTO DE ENTRADA =====
if __name__ == "__main__":
    print("🚀 Ejecutando Taskly...")
    app.run(debug=True)
