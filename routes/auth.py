from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Si el usuario ya está logueado, redirigir al home
    if 'user_id' in session:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validación básica de campos
        if not username or not password:
            flash('Por favor, complete todos los campos', 'error')
            return render_template('login.html')
        
        # Autenticación del usuario
        user = User.authenticate(username, password)
        
        if user:
            # Crear sesión del usuario
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['full_name'] = user.full_name
            session['role'] = user.role
            session['email'] = user.email
            
            flash(f'¡Bienvenido/a {user.full_name}!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    # Obtener nombre del usuario antes de limpiar la sesión
    user_name = session.get('full_name', 'Usuario')
    
    # Limpiar toda la sesión
    session.clear()
    
    flash(f'¡Hasta luego {user_name}! Has cerrado sesión correctamente', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de nuevos usuarios (opcional)"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', 'Participante')
        
        # Validaciones
        if not all([username, password, email, full_name]):
            flash('Todos los campos son obligatorios', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('register.html')
        
        # Crear nuevo usuario
        new_user = User(
            username=username,
            password=password,  # En producción, usar hash
            email=email,
            full_name=full_name,
            role=role
        )
        
        if new_user.save():
            flash('Usuario registrado exitosamente. Ya puedes iniciar sesión', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Error al registrar usuario. El username o email ya existe', 'error')
    
    return render_template('register.html')

@auth_bp.route('/check_session')
def check_session():
    """Endpoint para verificar sesión activa (útil para AJAX)"""
    if 'user_id' in session:
        return {
            'logged_in': True,
            'user': {
                'id': session['user_id'],
                'username': session['username'],
                'full_name': session['full_name'],
                'role': session['role']
            }
        }
    return {'logged_in': False}

# Decorador para verificar autenticación
def login_required(f):
    """Decorador para rutas que requieren autenticación"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para verificar rol de organizador
def organizer_required(f):
    """Decorador para rutas que requieren rol de Organizador"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión', 'warning')
            return redirect(url_for('auth.login'))
        
        if session.get('role') != 'Organizador':
            flash('No tienes permisos para acceder a esta función', 'error')
            return redirect(url_for('main.home'))
        
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Cambiar contraseña del usuario actual"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validaciones
        if not all([current_password, new_password, confirm_password]):
            flash('Todos los campos son obligatorios', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('Las nuevas contraseñas no coinciden', 'error')
            return render_template('change_password.html')
        
        if len(new_password) < 6:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('change_password.html')
        
        # Verificar contraseña actual
        user = User.authenticate(session['username'], current_password)
        if not user:
            flash('La contraseña actual es incorrecta', 'error')
            return render_template('change_password.html')
        
        # Actualizar contraseña
        user.password = new_password
        if user.save():
            flash('Contraseña actualizada exitosamente', 'success')
            return redirect(url_for('main.profile'))
        else:
            flash('Error al actualizar la contraseña', 'error')
    
    return render_template('change_password.html')

@auth_bp.route('/profile_update', methods=['POST'])
@login_required
def profile_update():
    """Actualizar información del perfil"""
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    
    if not all([full_name, email]):
        flash('Todos los campos son obligatorios', 'error')
        return redirect(url_for('main.profile'))
    
    # Obtener usuario actual
    user = User.authenticate(session['username'], request.form.get('password', ''))
    if not user:
        flash('Contraseña incorrecta para confirmar cambios', 'error')
        return redirect(url_for('main.profile'))
    
    # Actualizar datos
    user.full_name = full_name
    user.email = email
    
    if user.save():
        # Actualizar sesión
        session['full_name'] = full_name
        session['email'] = email
        flash('Perfil actualizado exitosamente', 'success')
    else:
        flash('Error al actualizar el perfil', 'error')
    
    return redirect(url_for('main.profile'))