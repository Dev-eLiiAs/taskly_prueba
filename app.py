from flask import Flask, render_template, session, redirect, url_for, flash
import os
from datetime import datetime
import traceback
import uuid
from jinja2.exceptions import TemplateNotFound

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

# ===== IMPORTACIONES ADICIONALES =====
try:
    import flask
    flask_version = flask.__version__
except:
    flask_version = "Desconocida"

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
    
    return app

# Crear instancia de la aplicación
app = create_app()

# ===== CONTEXT PROCESSORS =====
@app.context_processor
def inject_user():
    """Hacer datos del usuario disponibles en todas las plantillas"""
    if 'user_id' in session:
        try:
            # Obtener contadores de tareas y eventos
            user_tasks = Task.get_by_user(session['user_id'])
            user_events = Event.get_by_user(session['user_id'])
            
            # Calcular estadísticas
            task_counts = {
                'total': len(user_tasks),
                'pending': len([t for t in user_tasks if t.status == 'pending']),
                'completed': len([t for t in user_tasks if t.status == 'completed']),
                'urgent': len([t for t in user_tasks if t.is_urgent() and t.status != 'completed'])
            }
            
            event_counts = {
                'total': len(user_events),
                'upcoming': len([e for e in user_events if e.event_date and e.event_date.date() >= datetime.now().date()]),
                'today': len([e for e in user_events if e.event_date and e.event_date.date() == datetime.now().date()])
            }
            
            return {
                'current_user': {
                    'user_id': session['user_id'],
                    'username': session['username'],
                    'full_name': session['full_name'],
                    'role': session['role'],
                    'email': session.get('email', '')
                },
                'is_organizer': session.get('role') == 'Organizador',
                'task_counts': task_counts,
                'event_counts': event_counts
            }
        except Exception as e:
            app.logger.error(f"Error en context processor: {e}")
            return {
                'current_user': None,
                'is_organizer': False,
                'task_counts': {'total': 0, 'pending': 0, 'completed': 0, 'urgent': 0},
                'event_counts': {'total': 0, 'upcoming': 0, 'today': 0}
            }
    
    return {
        'current_user': None,
        'is_organizer': False,
        'task_counts': {'total': 0, 'pending': 0, 'completed': 0, 'urgent': 0},
        'event_counts': {'total': 0, 'upcoming': 0, 'today': 0}
    }

@app.context_processor
def inject_globals():
    """Inyectar variables globales en todas las plantillas"""
    return {
        'app_name': 'Taskly',
        'app_version': '1.0.0',
        'current_year': datetime.now().year,
        'now': datetime.now()
    }

# ===== TEMPLATE FILTERS =====
@app.template_filter('datetime')
def datetime_filter(value, format='%d/%m/%Y %H:%M'):
    """Filtro para formatear fechas"""
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except:
            return value
    return value.strftime(format)

@app.template_filter('date')
def date_filter(value, format='%d/%m/%Y'):
    """Filtro para formatear solo fechas"""
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except:
            return value
    return value.strftime(format)

@app.template_filter('time')
def time_filter(value, format='%H:%M'):
    """Filtro para formatear solo horas"""
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except:
            return value
    return value.strftime(format)

@app.template_filter('relative_time')
def relative_time_filter(value):
    """Filtro para mostrar tiempo relativo"""
    if value is None:
        return ''
    
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except:
            return value
    
    now = datetime.now()
    diff = now - value
    
    if diff.days > 7:
        return value.strftime('%d/%m/%Y')
    elif diff.days > 0:
        return f"Hace {diff.days} día{'s' if diff.days != 1 else ''}"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"Hace {hours} hora{'s' if hours != 1 else ''}"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"Hace {minutes} minuto{'s' if minutes != 1 else ''}"
    else:
        return "Hace un momento"

@app.template_filter('priority_color')
def priority_color_filter(priority):
    """Filtro para obtener color según prioridad"""
    colors = {
        'high': 'danger',
        'medium': 'warning',
        'low': 'success'
    }
    return colors.get(priority, 'secondary')

@app.template_filter('status_color')
def status_color_filter(status):
    """Filtro para obtener color según estado"""
    colors = {
        'completed': 'success',
        'in_progress': 'warning',
        'pending': 'secondary'
    }
    return colors.get(status, 'secondary')

@app.template_filter('truncate_words')
def truncate_words_filter(text, length=50):
    """Filtro para truncar texto por palabras"""
    if not text:
        return ''
    
    if len(text) <= length:
        return text
    
    return text[:length].rsplit(' ', 1)[0] + '...'

# ===== MANEJO DE ERRORES =====
def get_error_info(error_code, error_type, exception=None):
    """Obtener información del error según el tipo"""
    error_configs = {
        '404': {
            'title': 'Página no encontrada',
            'description': 'La página que buscas no existe o ha sido movida a otra ubicación.',
            'type': '404'
        },
        '403': {
            'title': 'Acceso denegado',
            'description': 'No tienes los permisos necesarios para acceder a esta página.',
            'type': '403'
        },
        '500': {
            'title': 'Error interno del servidor',
            'description': 'Ha ocurrido un error interno en el servidor. Nuestro equipo ha sido notificado.',
            'type': '500'
        },
        'template': {
            'title': 'Plantilla no encontrada',
            'description': 'La página solicitada tiene un problema técnico. El archivo de plantilla no se pudo encontrar.',
            'type': 'template'
        },
        'default': {
            'title': 'Error inesperado',
            'description': 'Ha ocurrido un error inesperado. Por favor, inténtalo de nuevo más tarde.',
            'type': 'default'
        }
    }
    
    return error_configs.get(str(error_code), error_configs['default'])

def render_error_page(error_code, error_type='default', exception=None, technical_details=None):
    """Renderizar página de error universal"""
    try:
        error_info = get_error_info(error_code, error_type, exception)
        error_id = str(uuid.uuid4())[:8]  # ID único para tracking

        # Determinar si es un error crítico
        is_critical = False
        try:
            is_critical = int(error_code) >= 500
        except (ValueError, TypeError):
            is_critical = str(error_code) in ['Template', 'default']        
        
        # Preparar detalles técnicos
        tech_details = technical_details or {}
        error_traceback = None
        
        if exception and app.debug:
            if hasattr(exception, 'original_exception'):
                error_traceback = ''.join(traceback.format_exception(
                    type(exception.original_exception),
                    exception.original_exception,
                    exception.original_exception.__traceback__
                ))
            else:
                error_traceback = ''.join(traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                ))
        
        # Log del error
        log_message = f"Error {error_code} ({error_type}) - ID: {error_id}"
        if exception:
            log_message += f" - {str(exception)}"
        
        app.logger.error(log_message, exc_info=exception if app.debug else False)
        
        context = {
            'error_code': error_code,
            'error_type': error_info['type'],
            'error_title': error_info['title'],
            'error_description': error_info['description'],
            'error_id': error_id,
            'technical_details': tech_details,
            'error_traceback': error_traceback,
            'now': datetime.now()
        }
        
        return render_template('errors/error.html', **context), error_code
        
    except Exception as e:
        # Si la página de error falla, mostrar error básico
        app.logger.error(f'Error crítico en manejador de errores: {e}')
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error crítico - Taskly</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    margin: 50px; 
                    background: #f8f9fa;
                }}
                .error-box {{ 
                    background: white; 
                    padding: 2rem; 
                    border-radius: 10px; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    max-width: 500px;
                    margin: 0 auto;
                }}
                .error-code {{ color: #dc3545; font-size: 2rem; font-weight: bold; }}
                .btn {{ 
                    background: #007bff; 
                    color: white; 
                    padding: 10px 20px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    display: inline-block; 
                    margin-top: 1rem;
                }}
            </style>
        </head>
        <body>
            <div class="error-box">
                <div class="error-code">{error_code}</div>
                <h2>Error crítico del sistema</h2>
                <p>Ha ocurrido un error crítico. Por favor, contacta al administrador.</p>
                <a href="/" class="btn">Volver al inicio</a>
            </div>
        </body>
        </html>
        ''', error_code or 500

# Manejadores específicos de errores
@app.errorhandler(404)
def not_found_error(error):
    """Error 404 - Página no encontrada"""
    return render_error_page(404, '404', error)

@app.errorhandler(403)
def forbidden_error(error):
    """Error 403 - Acceso denegado"""
    return render_error_page(403, '403', error)

@app.errorhandler(500)
def internal_error(error):
    """Error 500 - Error interno del servidor"""
    return render_error_page(500, '500', error)

@app.errorhandler(TemplateNotFound)
def template_not_found_error(error):
    """Error de plantilla no encontrada"""
    template_name = str(error).split("'")[1] if "'" in str(error) else "Desconocido"
    
    technical_details = {
        'Plantilla faltante': template_name,
        'Rutas buscadas': getattr(error, 'searched_for', ['No disponible'])
    }
    
    return render_error_page('Template', 'template', error, technical_details)

# ===== BEFORE/AFTER REQUEST =====
@app.before_request
def before_request():
    """Ejecutar antes de cada request"""
    # Verificar conexión a base de datos
    try:
        db = Database()
        conn = db.get_connection()
        if not conn:
            flash('Error de conexión a la base de datos', 'error')
            return redirect(url_for('auth.login'))
        db.close_connection()
    except Exception as e:
        app.logger.error(f"Error de base de datos: {e}")
        if not request.endpoint or request.endpoint != 'auth.login':
            flash('Error de sistema. Por favor, inténtalo más tarde.', 'error')
            return redirect(url_for('auth.login'))

@app.after_request
def after_request(response):
    """Ejecutar después de cada request"""
    # Agregar headers de seguridad
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # En desarrollo, deshabilitar caché
    if app.debug:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

# ===== COMANDOS CLI =====
@app.cli.command()
def init_db():
    """Inicializar base de datos con datos de prueba"""
    try:
        print("🔧 Inicializando base de datos...")
        
        # Crear base de datos y tablas
        if create_database_and_tables():
            print("✅ Base de datos inicializada correctamente")
        else:
            print("❌ Error inicializando base de datos")
            
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")

@app.cli.command()
def create_sample_data():
    """Crear datos de muestra para testing"""
    try:
        # Crear tareas de muestra
        sample_tasks = [
            {
                'title': 'Revisar documentación del proyecto',
                'description': 'Revisar y actualizar la documentación técnica',
                'priority': 'high',
                'status': 'pending',
                'user_id': 1
            },
            {
                'title': 'Preparar presentación',
                'description': 'Crear presentación para la reunión del equipo',
                'priority': 'medium',
                'status': 'in_progress',
                'user_id': 1
            },
            {
                'title': 'Backup de datos',
                'description': 'Realizar backup semanal de la base de datos',
                'priority': 'low',
                'status': 'completed',
                'user_id': 1
            }
        ]
        
        for task_data in sample_tasks:
            task = Task(
                title=task_data['title'],
                description=task_data['description'],
                priority=task_data['priority'],
                status=task_data['status'],
                user_id=task_data['user_id']
            )
            task.save()
        
        # Crear eventos de muestra
        from datetime import timedelta
        tomorrow = datetime.now() + timedelta(days=1)
        
        sample_events = [
            {
                'title': 'Reunión de equipo',
                'description': 'Reunión semanal del equipo de desarrollo',
                'event_date': tomorrow.replace(hour=10, minute=0),
                'location': 'Sala de reuniones',
                'user_id': 1
            },
            {
                'title': 'Presentación del proyecto',
                'description': 'Presentación final del proyecto a los stakeholders',
                'event_date': tomorrow.replace(hour=15, minute=30),
                'location': 'Auditorio principal',
                'user_id': 1
            }
        ]
        
        for event_data in sample_events:
            event = Event(
                title=event_data['title'],
                description=event_data['description'],
                event_date=event_data['event_date'],
                location=event_data['location'],
                user_id=event_data['user_id']
            )
            event.save()
        
        print("✅ Datos de muestra creados correctamente")
        
    except Exception as e:
        print(f"❌ Error creando datos de muestra: {e}")

@app.cli.command()
def clean_cache():
    """Limpiar archivos de caché y temporales"""
    import shutil
    
    try:
        # Limpiar caché de Flask
        cache_dir = os.path.join(app.instance_path, 'cache')
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
        
        # Limpiar archivos de sesión
        session_dir = os.path.join(app.instance_path, 'flask_session')
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
        
        print("✅ Caché limpiado correctamente")
        
    except Exception as e:
        print(f"❌ Error limpiando caché: {e}")

# ===== FUNCIONES DE UTILIDAD =====
def get_db_stats():
    """Obtener estadísticas de la base de datos"""
    try:
        db = Database()
        conn = db.get_connection()
        
        with conn.cursor() as cursor:
            stats = {}
            
            # Contar usuarios
            cursor.execute("SELECT COUNT(*) as count FROM users")
            stats['users'] = cursor.fetchone()['count']
            
            # Contar tareas
            cursor.execute("SELECT COUNT(*) as count FROM tasks")
            stats['tasks'] = cursor.fetchone()['count']
            
            # Contar eventos
            cursor.execute("SELECT COUNT(*) as count FROM events")
            stats['events'] = cursor.fetchone()['count']
            
            # Tareas por estado
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM tasks 
                GROUP BY status
            """)
            stats['tasks_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # Usuarios por rol
            cursor.execute("""
                SELECT role, COUNT(*) as count 
                FROM users 
                GROUP BY role
            """)
            stats['users_by_role'] = {row['role']: row['count'] for row in cursor.fetchall()}
        
        db.close_connection()
        return stats
        
    except Exception as e:
        app.logger.error(f"Error obteniendo estadísticas: {e}")
        return {}

# ===== CONFIGURACIÓN DE LOGGING =====
if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    
    # Crear directorio de logs si no existe
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Configurar archivo de log
    file_handler = RotatingFileHandler('logs/taskly.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Taskly startup')

# ===== RUTAS ADICIONALES =====
@app.route('/api/health')
def health_check():
    """Endpoint para verificar el estado de la aplicación"""
    try:
        # Verificar conexión a base de datos
        db = Database()
        conn = db.get_connection()
        db.close_connection()
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'database': 'connected'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }, 500

@app.route('/api/stats')
def api_stats():
    """Endpoint para obtener estadísticas de la aplicación"""
    if 'user_id' not in session:
        return {'error': 'No autorizado'}, 401
    
    if session.get('role') != 'Organizador':
        return {'error': 'Permisos insuficientes'}, 403
    
    stats = get_db_stats()
    return {
        'success': True,
        'stats': stats,
        'timestamp': datetime.now().isoformat()
    }

# ===== PUNTO DE ENTRADA =====
if __name__ == '__main__':
    # Configurar puerto y host
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("🚀 Iniciando Taskly...")
    print(f"📍 URL: http://{host}:{port}")
    print(f"🔧 Debug: {debug}")
    print(f"📊 Base de datos: {Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}")
    
    # Verificar/crear base de datos y conexión inicial
    try:
        # Intentar crear la base de datos si no existe
        if not verify_database_connection():
            print("🔧 Base de datos no encontrada, intentando crear...")
            if not create_database_and_tables():
                print("❌ Error: No se pudo crear la base de datos")
                print("🔧 Verifica la configuración en config.py")
                exit(1)
        
        # Verificar conexión final
        db = Database()
        conn = db.get_connection()
        if conn:
            print("✅ Conexión a base de datos exitosa")
            db.close_connection()
        else:
            print("❌ Error: No se pudo conectar a la base de datos")
            print("🔧 Verifica la configuración en config.py")
            exit(1)
            
    except Exception as e:
        print(f"Error connecting to database: {e}")
        
        # Intentar crear la base de datos como último recurso
        try:
            print("🔄 Intentando crear base de datos...")
            if create_database_and_tables():
                print("✅ Base de datos creada, reintentando conexión...")
                db = Database()
                conn = db.get_connection()
                if conn:
                    print("✅ Conexión exitosa después de crear la base de datos")
                    db.close_connection()
                else:
                    raise Exception("No se pudo conectar después de crear la base de datos")
            else:
                raise Exception("No se pudo crear la base de datos")
        except Exception as creation_error:
            print(f"❌ Error: {creation_error}")
            print("🔧 Verifica que MySQL esté ejecutándose y la configuración sea correcta")
            print("💡 También puedes ejecutar manualmente: mysql -u root -p < database.sql")
            exit(1)
    
    # Verificar que existan las tablas necesarias
    try:
        db = Database()
        conn = db.get_connection()
        
        with conn.cursor() as cursor:
            # Verificar tabla users
            cursor.execute("SHOW TABLES LIKE 'users'")
            if not cursor.fetchone():
                print("⚠️  Advertencia: Tabla 'users' no encontrada")
                print("💡 Ejecuta 'flask init-db' para crear las tablas")
            
            # Verificar tabla tasks
            cursor.execute("SHOW TABLES LIKE 'tasks'")
            if not cursor.fetchone():
                print("⚠️  Advertencia: Tabla 'tasks' no encontrada")
            
            # Verificar tabla events
            cursor.execute("SHOW TABLES LIKE 'events'")
            if not cursor.fetchone():
                print("⚠️  Advertencia: Tabla 'events' no encontrada")
        
        db.close_connection()
    except Exception as e:
        print(f"⚠️  Advertencia: No se pudieron verificar las tablas: {e}")
    
    # Crear directorio de instancia si no existe
    if not os.path.exists(app.instance_path):
        try:
            os.makedirs(app.instance_path)
            print(f"📁 Directorio de instancia creado: {app.instance_path}")
        except Exception as e:
            print(f"⚠️  No se pudo crear directorio de instancia: {e}")
    
    # Crear directorio de logs si no existe
    if not os.path.exists('logs'):
        try:
            os.makedirs('logs')
            print("📁 Directorio de logs creado")
        except Exception as e:
            print(f"⚠️  No se pudo crear directorio de logs: {e}")
    
    # Configurar variables de entorno de desarrollo
    if debug:
        os.environ['FLASK_APP'] = 'app.py'
        os.environ['FLASK_ENV'] = 'development'
        print("🔧 Modo desarrollo activado")
        print("📝 Recarga automática habilitada")
        print("🐛 Debugging habilitado")
        
        # Mostrar rutas disponibles en modo debug
        print("\n📍 Rutas disponibles:")
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
            print(f"   {rule.endpoint:25} {methods:15} {rule.rule}")
    
    # Mostrar información adicional
    print(f"\n📋 Información del sistema:")
    print(f"   Python: {os.sys.version.split()[0]}")
    print(f"   Flask: {flask_version}")
    print(f"   Zona horaria: {datetime.now().astimezone().tzinfo}")
    
    # Ejecutar aplicación
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=debug
        )
    except KeyboardInterrupt:
        print("\n👋 Cerrando Taskly...")
        print("✅ Aplicación cerrada correctamente")
    except Exception as e:
        print(f"\n❌ Error ejecutando la aplicación: {e}")
        exit(1)

# ===== FUNCIONES DE DESARROLLO =====
def print_app_info():
    """Mostrar información completa de la aplicación"""
    print("\n" + "="*60)
    print("🎯 TASKLY - SISTEMA DE GESTIÓN DE TAREAS Y EVENTOS")
    print("="*60)
    print(f"📅 Versión: 1.0.0")
    print(f"🏗️  Framework: Flask {flask_version}")
    print(f"🐍 Python: {os.sys.version.split()[0]}")
    print(f"📊 Base de datos: MySQL")
    print(f"🌐 Host: {os.environ.get('HOST', '127.0.0.1')}")
    print(f"🚪 Puerto: {os.environ.get('PORT', 5000)}")
    print(f"🔧 Debug: {os.environ.get('FLASK_DEBUG', 'True')}")
    print("="*60)
    
    # Mostrar estadísticas si hay datos
    try:
        stats = get_db_stats()
        if stats:
            print("📈 Estadísticas:")
            print(f"   👥 Usuarios: {stats.get('users', 0)}")
            print(f"   📋 Tareas: {stats.get('tasks', 0)}")
            print(f"   📅 Eventos: {stats.get('events', 0)}")
            
            if 'tasks_by_status' in stats:
                print("   📊 Tareas por estado:")
                for status, count in stats['tasks_by_status'].items():
                    print(f"      - {status}: {count}")
    except:
        pass
    
    print("="*60)

def validate_environment():
    """Validar que el entorno esté configurado correctamente"""
    issues = []
    
    # Verificar variables de entorno críticas
    if not Config.DB_NAME:
        issues.append("❌ DB_NAME no configurado")
    
    if not Config.DB_USER:
        issues.append("❌ DB_USER no configurado")
    
    if not Config.SECRET_KEY or Config.SECRET_KEY == 'dev-secret-key-taskly':
        issues.append("⚠️  SECRET_KEY usando valor por defecto (no seguro para producción)")
    
    # Verificar directorios necesarios
    required_dirs = ['static', 'templates', 'models', 'routes']
    for directory in required_dirs:
        if not os.path.exists(directory):
            issues.append(f"❌ Directorio requerido no encontrado: {directory}")
    
    # Verificar archivos críticos
    required_files = [
        'config.py',
        'models/database.py',
        'models/user.py',
        'models/task.py',
        'models/event.py',
        'routes/auth.py',
        'routes/main.py',
        'routes/tasks.py',
        'routes/events.py',
        'templates/base.html',
        'static/css/style.css',
        'static/js/main.js'
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            issues.append(f"❌ Archivo requerido no encontrado: {file_path}")
    
    if issues:
        print("\n🚨 PROBLEMAS DETECTADOS:")
        for issue in issues:
            print(f"   {issue}")
        print("\n💡 Resuelve estos problemas antes de continuar")
        return False
    else:
        print("✅ Entorno validado correctamente")
        return True



# Validar entorno al importar
if __name__ == '__main__':
    print_app_info()
    
    if not validate_environment():
        print("\n❌ Validación de entorno fallida")
        exit(1)
    
    print("✅ Entorno validado - Iniciando aplicación...\n")

# ===== CONFIGURACIÓN DE SEGURIDAD ADICIONAL =====
@app.before_first_request
def configure_security():
    """Configurar medidas de seguridad adicionales"""
    if not app.debug:
        # Configurar headers de seguridad estrictos para producción
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        
        # Configurar CSP (Content Security Policy)
        app.config['CONTENT_SECURITY_POLICY'] = {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com",
            'style-src': "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            'font-src': "'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com",
            'img-src': "'self' data: https:",
            'connect-src': "'self'"
        }

# ===== MANEJO DE SEÑALES =====
import signal
import sys

def signal_handler(sig, frame):
    """Manejar señales del sistema para cierre graceful"""
    print(f"\n📡 Señal recibida: {sig}")
    print("🔄 Cerrando conexiones...")
    
    # Cerrar conexiones de base de datos activas
    try:
        # Aquí se pueden agregar limpiezas adicionales
        pass
    except Exception as e:
        print(f"⚠️  Error durante limpieza: {e}")
    
    print("👋 Taskly cerrado correctamente")
    sys.exit(0)

# Registrar manejadores de señales
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ===== MIDDLEWARE PERSONALIZADO =====
class SecurityMiddleware:
    """Middleware para agregar headers de seguridad"""
    
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        def new_start_response(status, response_headers):
            # Agregar headers de seguridad
            response_headers.append(('X-Content-Type-Options', 'nosniff'))
            response_headers.append(('X-Frame-Options', 'DENY'))
            response_headers.append(('X-XSS-Protection', '1; mode=block'))
            response_headers.append(('Referrer-Policy', 'strict-origin-when-cross-origin'))
            
            return start_response(status, response_headers)
        
        return self.app(environ, new_start_response)

# Aplicar middleware en producción
if not app.debug:
    app.wsgi_app = SecurityMiddleware(app.wsgi_app)

# ===== INFORMACIÓN FINAL =====
print("📚 app.py cargado correctamente")
if __name__ == '__main__':
    print("🎯 Listo para ejecutar con: python app.py")