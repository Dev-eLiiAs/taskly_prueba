from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from models.user import User
from models.task import Task
from models.event import Event
from routes.auth import login_required, organizer_required
from datetime import datetime, date, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Página de inicio - redirige según estado de sesión"""
    if 'user_id' in session:
        return redirect(url_for('main.home'))
    return redirect(url_for('auth.login'))

@main_bp.route('/home')
@login_required
def home():
    """Dashboard principal de la aplicación"""
    user_id = session['user_id']
    
    # Obtener estadísticas del usuario
    recent_tasks = Task.get_by_user(user_id)[:5]  # Últimas 5 tareas
    upcoming_events = Event.get_by_user(user_id)[:3]  # Próximos 3 eventos
    
    # Contar tareas por estado
    all_tasks = Task.get_by_user(user_id)
    task_stats = {
        'total': len(all_tasks),
        'pending': len([t for t in all_tasks if t.status == 'pending']),
        'in_progress': len([t for t in all_tasks if t.status == 'in_progress']),
        'completed': len([t for t in all_tasks if t.status == 'completed']),
        'urgent': len([t for t in all_tasks if t.is_urgent()])
    }
    
    # Tareas urgentes (próximas a vencer)
    urgent_tasks = [t for t in all_tasks if t.is_urgent() and t.status != 'completed']
    
    # Eventos de esta semana
    today = date.today()
    week_end = today + timedelta(days=7)
    this_week_events = []
    
    for event in Event.get_by_user(user_id):
        if event.event_date:
            event_date = event.event_date.date() if hasattr(event.event_date, 'date') else event.event_date
            if today <= event_date <= week_end:
                this_week_events.append(event)
    
    return render_template('home.html', 
                         recent_tasks=recent_tasks,
                         upcoming_events=upcoming_events,
                         task_stats=task_stats,
                         urgent_tasks=urgent_tasks,
                         this_week_events=this_week_events,
                         current_user=session)

@main_bp.route('/profile')
@login_required
def profile():
    """Página de perfil del usuario"""
    # Obtener información completa del usuario
    user = User.authenticate(session['username'], session.get('temp_password', ''))
    
    if not user:
        # Si no se puede obtener el usuario, usar datos de sesión
        user_data = {
            'user_id': session['user_id'],
            'username': session['username'],
            'full_name': session['full_name'],
            'email': session.get('email', ''),
            'role': session['role']
        }
    else:
        user_data = user.to_dict()
    
    # Estadísticas del usuario
    user_tasks = Task.get_by_user(session['user_id'])
    user_events = Event.get_by_user(session['user_id'])
    
    profile_stats = {
        'total_tasks': len(user_tasks),
        'completed_tasks': len([t for t in user_tasks if t.status == 'completed']),
        'total_events': len(user_events),
        'member_since': 'Miembro desde hace tiempo'  # Podrías calcular esto
    }
    
    return render_template('profile.html', 
                         user=user_data, 
                         stats=profile_stats)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Vista de dashboard con información resumida"""
    return redirect(url_for('main.home'))

@main_bp.route('/notifications')
@login_required
def notifications():
    """Sistema de notificaciones y alertas"""
    user_id = session['user_id']
    notifications = []
    
    # Notificaciones de tareas urgentes
    urgent_tasks = [t for t in Task.get_by_user(user_id) if t.is_urgent() and t.status != 'completed']
    for task in urgent_tasks:
        notifications.append({
            'type': 'warning',
            'title': 'Tarea Urgente',
            'message': f'La tarea "{task.title}" vence pronto',
            'date': task.due_date,
            'link': url_for('tasks.tasks'),
            'icon': 'fas fa-exclamation-triangle'
        })
    
    # Notificaciones de eventos próximos
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    for event in Event.get_by_user(user_id):
        if event.event_date:
            event_date = event.event_date.date() if hasattr(event.event_date, 'date') else event.event_date
            if event_date == tomorrow:
                notifications.append({
                    'type': 'info',
                    'title': 'Evento Mañana',
                    'message': f'Tienes el evento "{event.title}" mañana',
                    'date': event.event_date,
                    'link': url_for('events.event_calendar'),
                    'icon': 'fas fa-calendar-alt'
                })
    
    # Ordenar notificaciones por fecha
    notifications.sort(key=lambda x: x['date'] if x['date'] else date.today())
    
    return render_template('notifications.html', notifications=notifications)

@main_bp.route('/search')
@login_required
def search():
    """Búsqueda global de tareas y eventos"""
    query = request.args.get('q', '').strip()
    results = {'tasks': [], 'events': []}
    
    if query and len(query) >= 2:
        user_id = session['user_id']
        
        # Buscar en tareas
        all_tasks = Task.get_by_user(user_id)
        for task in all_tasks:
            if (query.lower() in task.title.lower() or 
                (task.description and query.lower() in task.description.lower())):
                results['tasks'].append(task)
        
        # Buscar en eventos
        all_events = Event.get_by_user(user_id)
        for event in all_events:
            if (query.lower() in event.title.lower() or 
                (event.description and query.lower() in event.description.lower()) or
                (event.location and query.lower() in event.location.lower())):
                results['events'].append(event)
    
    return render_template('search.html', 
                         query=query, 
                         results=results,
                         total_results=len(results['tasks']) + len(results['events']))

@main_bp.route('/api/quick_stats')
@login_required
def api_quick_stats():
    """API endpoint para obtener estadísticas rápidas (AJAX)"""
    user_id = session['user_id']
    
    tasks = Task.get_by_user(user_id)
    events = Event.get_by_user(user_id)
    
    stats = {
        'tasks': {
            'total': len(tasks),
            'pending': len([t for t in tasks if t.status == 'pending']),
            'completed': len([t for t in tasks if t.status == 'completed']),
            'urgent': len([t for t in tasks if t.is_urgent()])
        },
        'events': {
            'total': len(events),
            'this_week': len([e for e in events if e.event_date and 
                            e.event_date.date() >= date.today() and 
                            e.event_date.date() <= date.today() + timedelta(days=7)])
        }
    }
    
    return jsonify(stats)

@main_bp.route('/settings')
@login_required
def settings():
    """Página de configuración de la aplicación"""
    return render_template('settings.html')

@main_bp.route('/help')
@login_required
def help():
    """Página de ayuda y documentación"""
    help_sections = [
        {
            'title': 'Gestión de Tareas',
            'content': 'Aprende a crear, editar y organizar tus tareas por prioridad.',
            'icon': 'fas fa-tasks'
        },
        {
            'title': 'Gestión de Eventos',
            'content': 'Crea eventos con fecha, hora y ubicación para mantener tu calendario organizado.',
            'icon': 'fas fa-calendar'
        },
        {
            'title': 'Notificaciones',
            'content': 'Configura recordatorios automáticos para no perder fechas importantes.',
            'icon': 'fas fa-bell'
        },
        {
            'title': 'Roles de Usuario',
            'content': 'Entiende las diferencias entre roles de Organizador y Participante.',
            'icon': 'fas fa-users'
        }
    ]
    
    return render_template('help.html', help_sections=help_sections)

@main_bp.route('/about')
def about():
    """Página sobre la aplicación"""
    app_info = {
        'name': 'Taskly',
        'version': '1.0.0',
        'description': 'Sistema de gestión de tareas y eventos para mejorar tu productividad',
        'technologies': ['Python', 'Flask', 'MySQL', 'Bootstrap', 'JavaScript'],
        'features': [
            'Gestión completa de tareas con prioridades',
            'Calendario de eventos integrado',
            'Sistema de notificaciones automáticas',
            'Roles de usuario diferenciados',
            'Interfaz responsive y moderna'
        ]
    }
    
    return render_template('about.html', app_info=app_info)

@main_bp.route('/admin')
@organizer_required
def admin():
    """Panel de administración solo para Organizadores"""
    from models.database import Database
    
    # Estadísticas generales del sistema
    db = Database()
    conn = db.get_connection()
    
    try:
        with conn.cursor() as cursor:
            # Total de usuarios
            cursor.execute("SELECT COUNT(*) as total FROM users")
            total_users = cursor.fetchone()['total']
            
            # Total de tareas
            cursor.execute("SELECT COUNT(*) as total FROM tasks")
            total_tasks = cursor.fetchone()['total']
            
            # Total de eventos
            cursor.execute("SELECT COUNT(*) as total FROM events")
            total_events = cursor.fetchone()['total']
            
            # Usuarios por rol
            cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
            users_by_role = cursor.fetchall()
            
    except Exception as e:
        flash('Error al obtener estadísticas del sistema', 'error')
        total_users = total_tasks = total_events = 0
        users_by_role = []
    finally:
        db.close_connection()
    
    admin_stats = {
        'total_users': total_users,
        'total_tasks': total_tasks,
        'total_events': total_events,
        'users_by_role': users_by_role
    }
    
    return render_template('admin.html', stats=admin_stats)

# Context processor para hacer datos disponibles en todas las plantillas
@main_bp.app_context_processor
def inject_user():
    """Inyectar información del usuario en todas las plantillas"""
    if 'user_id' in session:
        return {
            'current_user': {
                'id': session['user_id'],
                'username': session['username'],
                'full_name': session['full_name'],
                'role': session['role'],
                'email': session.get('email', '')
            },
            'is_organizer': session.get('role') == 'Organizador'
        }
    return {}