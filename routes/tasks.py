from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.task import Task
from routes.auth import login_required, organizer_required
from datetime import datetime, date, timedelta
import json

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/tasks')
@login_required
def tasks():
    """Vista principal de gestión de tareas"""
    user_id = session['user_id']
    
    # Obtener filtros de la URL
    filter_status = request.args.get('status', 'all')
    filter_priority = request.args.get('priority', 'all')
    sort_by = request.args.get('sort', 'due_date')
    
    # Obtener todas las tareas del usuario
    all_tasks = Task.get_by_user(user_id)
    
    # Aplicar filtros
    filtered_tasks = all_tasks
    
    if filter_status != 'all':
        filtered_tasks = [t for t in filtered_tasks if t.status == filter_status]
    
    if filter_priority != 'all':
        filtered_tasks = [t for t in filtered_tasks if t.priority == filter_priority]
    
    # Aplicar ordenamiento
    if sort_by == 'due_date':
        filtered_tasks.sort(key=lambda x: x.due_date if x.due_date else date.max)
    elif sort_by == 'priority':
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        filtered_tasks.sort(key=lambda x: priority_order.get(x.priority, 4))
    elif sort_by == 'title':
        filtered_tasks.sort(key=lambda x: x.title.lower())
    elif sort_by == 'created':
        filtered_tasks.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
    
    # Estadísticas para el dashboard de tareas
    task_stats = {
        'total': len(all_tasks),
        'pending': len([t for t in all_tasks if t.status == 'pending']),
        'in_progress': len([t for t in all_tasks if t.status == 'in_progress']),
        'completed': len([t for t in all_tasks if t.status == 'completed']),
        'high_priority': len([t for t in all_tasks if t.priority == 'high']),
        'urgent': len([t for t in all_tasks if t.is_urgent() and t.status != 'completed'])
    }
    
    # Tareas próximas a vencer (urgentes)
    urgent_tasks = [t for t in all_tasks if t.is_urgent() and t.status != 'completed']
    
    return render_template('tasks.html', 
                         tasks=filtered_tasks,
                         task_stats=task_stats,
                         urgent_tasks=urgent_tasks,
                         current_filters={
                             'status': filter_status,
                             'priority': filter_priority,
                             'sort': sort_by
                         })

@tasks_bp.route('/tasks/add', methods=['GET', 'POST'])
@login_required
def add_task():
    """Crear nueva tarea"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date', '').strip()
        priority = request.form.get('priority', 'medium')
        status = request.form.get('status', 'pending')
        
        # Validaciones
        if not title:
            flash('El título de la tarea es obligatorio', 'error')
            return render_template('task_form.html', action='add')
        
        # Convertir fecha si se proporciona
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                # Verificar que la fecha no sea en el pasado
                if due_date < date.today():
                    flash('La fecha de vencimiento no puede ser en el pasado', 'warning')
            except ValueError:
                flash('Formato de fecha inválido', 'error')
                return render_template('task_form.html', action='add')
        
        # Asignar prioridad automática según urgencia
        if due_date:
            days_until_due = (due_date - date.today()).days
            if days_until_due <= 1:
                priority = 'high'
            elif days_until_due <= 3:
                priority = 'medium' if priority == 'low' else priority
        
        # Crear nueva tarea
        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            status=status,
            user_id=session['user_id']
        )
        
        if task.save():
            flash(f'Tarea "{title}" creada exitosamente', 'success')
            return redirect(url_for('tasks.tasks'))
        else:
            flash('Error al crear la tarea', 'error')
    
    return render_template('task_form.html', action='add')

@tasks_bp.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Editar tarea existente"""
    task = Task.get_by_id(task_id)
    
    if not task:
        flash('Tarea no encontrada', 'error')
        return redirect(url_for('tasks.tasks'))
    
    # Verificar que la tarea pertenece al usuario actual
    if task.user_id != session['user_id']:
        flash('No tienes permisos para editar esta tarea', 'error')
        return redirect(url_for('tasks.tasks'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date', '').strip()
        priority = request.form.get('priority', task.priority)
        status = request.form.get('status', task.status)
        
        # Validaciones
        if not title:
            flash('El título de la tarea es obligatorio', 'error')
            return render_template('task_form.html', action='edit', task=task)
        
        # Convertir fecha
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido', 'error')
                return render_template('task_form.html', action='edit', task=task)
        
        # Actualizar la tarea
        old_title = task.title
        task.title = title
        task.description = description
        task.due_date = due_date
        task.priority = priority
        task.status = status
        
        if task.save():
            flash(f'Tarea "{old_title}" actualizada exitosamente', 'success')
            return redirect(url_for('tasks.tasks'))
        else:
            flash('Error al actualizar la tarea', 'error')
    
    return render_template('task_form.html', action='edit', task=task)

@tasks_bp.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    """Eliminar tarea"""
    task = Task.get_by_id(task_id)
    
    if not task:
        flash('Tarea no encontrada', 'error')
        return redirect(url_for('tasks.tasks'))
    
    # Verificar permisos
    if task.user_id != session['user_id'] and session.get('role') != 'Organizador':
        flash('No tienes permisos para eliminar esta tarea', 'error')
        return redirect(url_for('tasks.tasks'))
    
    task_title = task.title
    if task.delete():
        flash(f'Tarea "{task_title}" eliminada exitosamente', 'success')
    else:
        flash('Error al eliminar la tarea', 'error')
    
    return redirect(url_for('tasks.tasks'))

@tasks_bp.route('/tasks/<int:task_id>/toggle_status', methods=['POST'])
@login_required
def toggle_task_status(task_id):
    """Cambiar rápidamente el estado de una tarea"""
    task = Task.get_by_id(task_id)
    
    if not task or task.user_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Tarea no encontrada o sin permisos'})
    
    # Ciclo de estados: pending -> in_progress -> completed -> pending
    status_cycle = {
        'pending': 'in_progress',
        'in_progress': 'completed',
        'completed': 'pending'
    }
    
    new_status = status_cycle.get(task.status, 'pending')
    task.status = new_status
    
    if task.save():
        return jsonify({
            'success': True, 
            'new_status': new_status,
            'status_text': {
                'pending': 'Pendiente',
                'in_progress': 'En Progreso',
                'completed': 'Completada'
            }.get(new_status, 'Desconocido')
        })
    else:
        return jsonify({'success': False, 'message': 'Error al actualizar el estado'})

@tasks_bp.route('/tasks/<int:task_id>/update_priority', methods=['POST'])
@login_required
def update_task_priority(task_id):
    """Actualizar prioridad de una tarea vía AJAX"""
    task = Task.get_by_id(task_id)
    
    if not task or task.user_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Tarea no encontrada o sin permisos'})
    
    new_priority = request.json.get('priority')
    if new_priority not in ['high', 'medium', 'low']:
        return jsonify({'success': False, 'message': 'Prioridad inválida'})
    
    task.priority = new_priority
    
    if task.save():
        return jsonify({
            'success': True,
            'new_priority': new_priority,
            'color_class': task.get_priority_color()
        })
    else:
        return jsonify({'success': False, 'message': 'Error al actualizar la prioridad'})

@tasks_bp.route('/tasks/bulk_action', methods=['POST'])
@login_required
def bulk_action():
    """Acciones en lote para múltiples tareas"""
    task_ids = request.form.getlist('task_ids')
    action = request.form.get('action')
    
    if not task_ids:
        flash('No se seleccionaron tareas', 'warning')
        return redirect(url_for('tasks.tasks'))
    
    success_count = 0
    
    for task_id in task_ids:
        task = Task.get_by_id(int(task_id))
        if not task or task.user_id != session['user_id']:
            continue
        
        if action == 'delete':
            if task.delete():
                success_count += 1
        elif action == 'complete':
            task.status = 'completed'
            if task.save():
                success_count += 1
        elif action == 'mark_pending':
            task.status = 'pending'
            if task.save():
                success_count += 1
        elif action == 'high_priority':
            task.priority = 'high'
            if task.save():
                success_count += 1
    
    if success_count > 0:
        action_names = {
            'delete': 'eliminadas',
            'complete': 'completadas',
            'mark_pending': 'marcadas como pendientes',
            'high_priority': 'marcadas como alta prioridad'
        }
        flash(f'{success_count} tareas {action_names.get(action, "procesadas")} exitosamente', 'success')
    else:
        flash('No se procesaron tareas', 'warning')
    
    return redirect(url_for('tasks.tasks'))

@tasks_bp.route('/tasks/export')
@login_required
def export_tasks():
    """Exportar tareas del usuario a CSV"""
    import csv
    from io import StringIO
    from flask import Response
    
    user_tasks = Task.get_by_user(session['user_id'])
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow(['Título', 'Descripción', 'Fecha Vencimiento', 'Prioridad', 'Estado', 'Fecha Creación'])
    
    # Datos
    for task in user_tasks:
        writer.writerow([
            task.title,
            task.description or '',
            task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
            task.priority,
            task.status,
            task.created_at.strftime('%Y-%m-%d %H:%M') if task.created_at else ''
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=mis_tareas.csv'}
    )

@tasks_bp.route('/tasks/statistics')
@login_required
def task_statistics():
    """Vista de estadísticas detalladas de tareas"""
    user_tasks = Task.get_by_user(session['user_id'])
    
    # Estadísticas por prioridad
    priority_stats = {
        'high': len([t for t in user_tasks if t.priority == 'high']),
        'medium': len([t for t in user_tasks if t.priority == 'medium']),
        'low': len([t for t in user_tasks if t.priority == 'low'])
    }
    
    # Estadísticas por estado
    status_stats = {
        'pending': len([t for t in user_tasks if t.status == 'pending']),
        'in_progress': len([t for t in user_tasks if t.status == 'in_progress']),
        'completed': len([t for t in user_tasks if t.status == 'completed'])
    }
    
    # Tareas por mes (últimos 6 meses)
    monthly_stats = {}
    for i in range(6):
        month_start = date.today().replace(day=1) - timedelta(days=i*30)
        month_tasks = [t for t in user_tasks if t.created_at and 
                      t.created_at.date().month == month_start.month]
        monthly_stats[month_start.strftime('%B')] = len(month_tasks)
    
    # Productividad (tareas completadas vs creadas)
    completed_tasks = [t for t in user_tasks if t.status == 'completed']
    productivity_rate = (len(completed_tasks) / len(user_tasks) * 100) if user_tasks else 0
    
    return render_template('task_statistics.html',
                         priority_stats=priority_stats,
                         status_stats=status_stats,
                         monthly_stats=monthly_stats,
                         productivity_rate=round(productivity_rate, 1),
                         total_tasks=len(user_tasks))

@tasks_bp.route('/api/tasks')
@login_required
def api_tasks():
    """API endpoint para obtener tareas (para uso con JavaScript)"""
    user_tasks = Task.get_by_user(session['user_id'])
    tasks_data = [task.to_dict() for task in user_tasks]
    
    return jsonify({
        'success': True,
        'tasks': tasks_data,
        'total': len(tasks_data)
    })

@tasks_bp.route('/tasks/urgent')
@login_required
def urgent_tasks():
    """Vista específica para tareas urgentes"""
    user_tasks = Task.get_by_user(session['user_id'])
    urgent_tasks = [t for t in user_tasks if t.is_urgent() and t.status != 'completed']
    
    return render_template('urgent_tasks.html', 
                         urgent_tasks=urgent_tasks,
                         total_urgent=len(urgent_tasks))

# Context processor específico para tareas
@tasks_bp.app_context_processor
def inject_task_counts():
    """Inyectar contadores de tareas en todas las plantillas"""
    if 'user_id' in session:
        user_tasks = Task.get_by_user(session['user_id'])
        return {
            'task_counts': {
                'total': len(user_tasks),
                'pending': len([t for t in user_tasks if t.status == 'pending']),
                'urgent': len([t for t in user_tasks if t.is_urgent() and t.status != 'completed'])
            }
        }
    return {}