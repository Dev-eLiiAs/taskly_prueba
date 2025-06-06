from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.event import Event
from models.task import Task
from routes.auth import login_required, organizer_required
from datetime import datetime, date, timedelta
import calendar
import json

events_bp = Blueprint('events', __name__)

@events_bp.route('/events')
@login_required
def events():
    """Vista principal de gestión de eventos"""
    user_id = session['user_id']
    
    # Obtener filtros de la URL
    view_type = request.args.get('view', 'list')  # list, calendar, upcoming
    month = request.args.get('month')
    year = request.args.get('year')
    
    # Obtener todos los eventos del usuario
    user_events = Event.get_by_user(user_id)
    
    # Filtrar por mes/año si se especifica
    filtered_events = user_events
    if month and year:
        try:
            target_month = int(month)
            target_year = int(year)
            filtered_events = [e for e in user_events if 
                             e.event_date and 
                             e.event_date.month == target_month and 
                             e.event_date.year == target_year]
        except ValueError:
            flash('Mes o año inválido', 'warning')
    
    # Eventos próximos (próximos 30 días)
    today = date.today()
    upcoming_events = [e for e in user_events if 
                      e.event_date and 
                      e.event_date.date() >= today and 
                      e.event_date.date() <= today + timedelta(days=30)]
    
    # Eventos de hoy
    today_events = [e for e in user_events if 
                   e.event_date and e.event_date.date() == today]
    
    # Estadísticas de eventos
    event_stats = {
        'total': len(user_events),
        'upcoming': len(upcoming_events),
        'today': len(today_events),
        'this_week': len([e for e in user_events if 
                         e.event_date and 
                         e.event_date.date() >= today and 
                         e.event_date.date() <= today + timedelta(days=7)]),
        'this_month': len([e for e in user_events if 
                          e.event_date and 
                          e.event_date.month == today.month and 
                          e.event_date.year == today.year])
    }
    
    return render_template('events.html',
                         events=filtered_events,
                         upcoming_events=upcoming_events,
                         today_events=today_events,
                         event_stats=event_stats,
                         view_type=view_type,
                         current_month=month,
                         current_year=year)

@events_bp.route('/calendar')
@login_required
def event_calendar():
    """Vista de calendario completo"""
    user_id = session['user_id']
    
    # Obtener mes y año actual o especificado
    now = datetime.now()
    month = int(request.args.get('month', now.month))
    year = int(request.args.get('year', now.year))
    
    # Validar mes y año
    if month < 1 or month > 12:
        month = now.month
    if year < 2020 or year > 2030:
        year = now.year
    
    # Obtener eventos del mes
    user_events = Event.get_by_user(user_id)
    month_events = [e for e in user_events if 
                   e.event_date and 
                   e.event_date.month == month and 
                   e.event_date.year == year]
    
    # Obtener tareas con fecha límite para el calendario
    user_tasks = Task.get_by_user(user_id)
    month_tasks = [t for t in user_tasks if 
                  t.due_date and 
                  t.due_date.month == month and 
                  t.due_date.year == year and
                  t.status != 'completed']
    
    # Generar estructura del calendario
    cal = calendar.monthcalendar(year, month)
    
    # Organizar eventos y tareas por día
    calendar_data = {}
    for week in cal:
        for day in week:
            if day == 0:
                continue
            calendar_data[day] = {
                'events': [e for e in month_events if e.event_date.day == day],
                'tasks': [t for t in month_tasks if t.due_date.day == day]
            }
    
    # Navegación del calendario
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    return render_template('calendar.html',
                         calendar_grid=cal,
                         calendar_data=calendar_data,
                         current_month=month,
                         current_year=year,
                         month_name=calendar.month_name[month],
                         prev_month=prev_month,
                         prev_year=prev_year,
                         next_month=next_month,
                         next_year=next_year,
                         today=date.today())

@events_bp.route('/events/add', methods=['GET', 'POST'])
@login_required
def add_event():
    """Crear nuevo evento"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        event_date_str = request.form.get('event_date', '').strip()
        event_time_str = request.form.get('event_time', '').strip()
        location = request.form.get('location', '').strip()
        
        # Validaciones
        if not title:
            flash('El título del evento es obligatorio', 'error')
            return render_template('event_form.html', action='add')
        
        if not event_date_str:
            flash('La fecha del evento es obligatoria', 'error')
            return render_template('event_form.html', action='add')
        
        # Procesar fecha y hora
        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
            
            # Si se proporciona hora, combinar con la fecha
            if event_time_str:
                event_time = datetime.strptime(event_time_str, '%H:%M').time()
                event_datetime = datetime.combine(event_date, event_time)
            else:
                # Si no hay hora, usar mediodía como default
                event_datetime = datetime.combine(event_date, datetime.min.time().replace(hour=12))
            
            # Verificar que el evento no sea en el pasado
            if event_datetime < datetime.now():
                flash('La fecha y hora del evento no puede ser en el pasado', 'warning')
                return render_template('event_form.html', action='add')
                
        except ValueError:
            flash('Formato de fecha u hora inválido', 'error')
            return render_template('event_form.html', action='add')
        
        # Crear nuevo evento
        event = Event(
            title=title,
            description=description,
            event_date=event_datetime,
            location=location,
            user_id=session['user_id']
        )
        
        if event.save():
            flash(f'Evento "{title}" creado exitosamente', 'success')
            
            # Si es un organizador, preguntar si quiere crear tarea asociada
            if session.get('role') == 'Organizador':
                return redirect(url_for('events.event_created', event_id=event.event_id))
            
            return redirect(url_for('events.event_calendar'))
        else:
            flash('Error al crear el evento', 'error')
    
    return render_template('event_form.html', action='add')

@events_bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    """Editar evento existente"""
    event = Event.get_by_id(event_id)
    
    if not event:
        flash('Evento no encontrado', 'error')
        return redirect(url_for('events.events'))
    
    # Verificar permisos
    if event.user_id != session['user_id'] and session.get('role') != 'Organizador':
        flash('No tienes permisos para editar este evento', 'error')
        return redirect(url_for('events.events'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        event_date_str = request.form.get('event_date', '').strip()
        event_time_str = request.form.get('event_time', '').strip()
        location = request.form.get('location', '').strip()
        
        # Validaciones
        if not title:
            flash('El título del evento es obligatorio', 'error')
            return render_template('event_form.html', action='edit', event=event)
        
        if not event_date_str:
            flash('La fecha del evento es obligatoria', 'error')
            return render_template('event_form.html', action='edit', event=event)
        
        # Procesar fecha y hora
        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
            
            if event_time_str:
                event_time = datetime.strptime(event_time_str, '%H:%M').time()
                event_datetime = datetime.combine(event_date, event_time)
            else:
                # Mantener la hora original si no se especifica nueva
                if event.event_date:
                    event_datetime = datetime.combine(event_date, event.event_date.time())
                else:
                    event_datetime = datetime.combine(event_date, datetime.min.time().replace(hour=12))
                    
        except ValueError:
            flash('Formato de fecha u hora inválido', 'error')
            return render_template('event_form.html', action='edit', event=event)
        
        # Actualizar evento
        old_title = event.title
        event.title = title
        event.description = description
        event.event_date = event_datetime
        event.location = location
        
        if event.save():
            flash(f'Evento "{old_title}" actualizado exitosamente', 'success')
            return redirect(url_for('events.event_calendar'))
        else:
            flash('Error al actualizar el evento', 'error')
    
    return render_template('event_form.html', action='edit', event=event)

@events_bp.route('/events/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    """Eliminar evento"""
    event = Event.get_by_id(event_id)
    
    if not event:
        flash('Evento no encontrado', 'error')
        return redirect(url_for('events.events'))
    
    # Verificar permisos
    if event.user_id != session['user_id'] and session.get('role') != 'Organizador':
        flash('No tienes permisos para eliminar este evento', 'error')
        return redirect(url_for('events.events'))
    
    event_title = event.title
    if event.delete():
        flash(f'Evento "{event_title}" eliminado exitosamente', 'success')
    else:
        flash('Error al eliminar el evento', 'error')
    
    return redirect(url_for('events.event_calendar'))

@events_bp.route('/events/<int:event_id>/view')
@login_required
def view_event(event_id):
    """Ver detalles completos de un evento"""
    event = Event.get_by_id(event_id)
    
    if not event:
        flash('Evento no encontrado', 'error')
        return redirect(url_for('events.events'))
    
    # Verificar permisos (cualquier usuario puede ver eventos)
    if event.user_id != session['user_id'] and session.get('role') != 'Organizador':
        flash('No tienes permisos para ver este evento', 'error')
        return redirect(url_for('events.events'))
    
    # Calcular tiempo restante
    time_until_event = None
    is_past_event = False
    
    if event.event_date:
        now = datetime.now()
        if event.event_date > now:
            delta = event.event_date - now
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            
            if days > 0:
                time_until_event = f"{days} días, {hours} horas"
            elif hours > 0:
                time_until_event = f"{hours} horas, {minutes} minutos"
            else:
                time_until_event = f"{minutes} minutos"
        else:
            is_past_event = True
    
    return render_template('event_detail.html',
                         event=event,
                         time_until_event=time_until_event,
                         is_past_event=is_past_event)

@events_bp.route('/events/<int:event_id>/created')
@login_required
@organizer_required
def event_created(event_id):
    """Página post-creación para organizadores"""
    event = Event.get_by_id(event_id)
    
    if not event or event.user_id != session['user_id']:
        return redirect(url_for('events.event_calendar'))
    
    return render_template('event_created.html', event=event)

@events_bp.route('/events/<int:event_id>/create_task', methods=['POST'])
@login_required
@organizer_required
def create_task_from_event(event_id):
    """Crear tarea asociada a un evento"""
    event = Event.get_by_id(event_id)
    
    if not event or event.user_id != session['user_id']:
        flash('Evento no encontrado', 'error')
        return redirect(url_for('events.event_calendar'))
    
    # Crear tarea automáticamente
    task_title = f"Preparar: {event.title}"
    task_description = f"Tarea de preparación para el evento '{event.title}' el {event.event_date.strftime('%d/%m/%Y %H:%M')}"
    
    # Fecha límite un día antes del evento
    due_date = event.event_date.date() - timedelta(days=1)
    
    task = Task(
        title=task_title,
        description=task_description,
        due_date=due_date,
        priority='high',
        status='pending',
        user_id=session['user_id']
    )
    
    if task.save():
        flash(f'Tarea "{task_title}" creada automáticamente', 'success')
    else:
        flash('Error al crear la tarea asociada', 'error')
    
    return redirect(url_for('events.event_calendar'))

@events_bp.route('/api/events')
@login_required
def api_events():
    """API endpoint para obtener eventos (para calendario JavaScript)"""
    user_events = Event.get_by_user(session['user_id'])
    
    events_data = []
    for event in user_events:
        events_data.append({
            'id': event.event_id,
            'title': event.title,
            'start': event.event_date.isoformat() if event.event_date else None,
            'description': event.description,
            'location': event.location,
            'url': url_for('events.view_event', event_id=event.event_id)
        })
    
    return jsonify(events_data)

@events_bp.route('/api/events/month/<int:year>/<int:month>')
@login_required
def api_events_month(year, month):
    """API para obtener eventos de un mes específico"""
    user_events = Event.get_by_user(session['user_id'])
    month_events = [e for e in user_events if 
                   e.event_date and 
                   e.event_date.month == month and 
                   e.event_date.year == year]
    
    events_data = [event.to_dict() for event in month_events]
    
    return jsonify({
        'success': True,
        'events': events_data,
        'total': len(events_data)
    })

@events_bp.route('/events/notifications')
@login_required
def event_notifications():
    """Obtener notificaciones de eventos próximos"""
    user_events = Event.get_by_user(session['user_id'])
    notifications = []
    
    now = datetime.now()
    
    for event in user_events:
        if not event.event_date or event.event_date <= now:
            continue
        
        # Calcular tiempo hasta el evento
        time_diff = event.event_date - now
        
        # Notificar eventos en las próximas 24 horas
        if time_diff.total_seconds() <= 24 * 3600:  # 24 horas
            if time_diff.total_seconds() <= 3600:  # 1 hora
                urgency = 'urgent'
                message = f"¡El evento '{event.title}' es en menos de 1 hora!"
            elif time_diff.total_seconds() <= 6 * 3600:  # 6 horas
                urgency = 'warning'
                hours = int(time_diff.total_seconds() // 3600)
                message = f"El evento '{event.title}' es en {hours} horas"
            else:
                urgency = 'info'
                message = f"El evento '{event.title}' es mañana"
            
            notifications.append({
                'event_id': event.event_id,
                'title': event.title,
                'message': message,
                'urgency': urgency,
                'event_date': event.event_date,
                'location': event.location
            })
    
    return jsonify({
        'success': True,
        'notifications': notifications,
        'count': len(notifications)
    })

@events_bp.route('/events/upcoming')
@login_required
def upcoming_events():
    """Vista de eventos próximos"""
    user_events = Event.get_by_user(session['user_id'])
    
    now = datetime.now()
    upcoming = [e for e in user_events if e.event_date and e.event_date > now]
    
    # Agrupar por tiempo
    today_events = [e for e in upcoming if e.event_date.date() == now.date()]
    tomorrow_events = [e for e in upcoming if e.event_date.date() == (now + timedelta(days=1)).date()]
    this_week_events = [e for e in upcoming if 
                       e.event_date.date() > (now + timedelta(days=1)).date() and
                       e.event_date.date() <= (now + timedelta(days=7)).date()]
    later_events = [e for e in upcoming if 
                   e.event_date.date() > (now + timedelta(days=7)).date()]
    
    return render_template('upcoming_events.html',
                         today_events=today_events,
                         tomorrow_events=tomorrow_events,
                         this_week_events=this_week_events,
                         later_events=later_events)

@events_bp.route('/events/export')
@login_required
def export_events():
    """Exportar eventos a formato ICS (Calendar)"""
    user_events = Event.get_by_user(session['user_id'])
    
    # Crear contenido ICS básico
    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Taskly//Event Calendar//EN\n"
    
    for event in user_events:
        if event.event_date:
            ics_content += "BEGIN:VEVENT\n"
            ics_content += f"UID:{event.event_id}@taskly.com\n"
            ics_content += f"DTSTART:{event.event_date.strftime('%Y%m%dT%H%M%S')}\n"
            ics_content += f"SUMMARY:{event.title}\n"
            if event.description:
                ics_content += f"DESCRIPTION:{event.description}\n"
            if event.location:
                ics_content += f"LOCATION:{event.location}\n"
            ics_content += "END:VEVENT\n"
    
    ics_content += "END:VCALENDAR"
    
    from flask import Response
    return Response(
        ics_content,
        mimetype='text/calendar',
        headers={'Content-Disposition': 'attachment; filename=mis_eventos.ics'}
    )

# Context processor específico para eventos
@events_bp.app_context_processor
def inject_event_counts():
    """Inyectar contadores de eventos en todas las plantillas"""
    if 'user_id' in session:
        user_events = Event.get_by_user(session['user_id'])
        today = date.today()
        
        upcoming_events = [e for e in user_events if 
                          e.event_date and e.event_date.date() >= today]
        
        return {
            'event_counts': {
                'total': len(user_events),
                'upcoming': len(upcoming_events),
                'today': len([e for e in user_events if 
                            e.event_date and e.event_date.date() == today])
            }
        }
    return {}