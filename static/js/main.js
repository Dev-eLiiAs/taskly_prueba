/* ===== TASKLY - MAIN JAVASCRIPT FILE ===== */

// Variables globales
let isLoading = false;
let notificationCount = 0;
let currentTheme = localStorage.getItem('taskly-theme') || 'light';

// Inicialización cuando el DOM esté listo
$(document).ready(function() {
    initializeApp();
});

// ===== INICIALIZACIÓN DE LA APLICACIÓN =====
function initializeApp() {
    console.log('🚀 Inicializando Taskly...');
    
    // Inicializar componentes básicos
    initializeTooltips();
    initializePopovers();
    initializeModals();
    initializeTheme();
    
    // Cargar datos del usuario si existe
    if (window.TASKLY && window.TASKLY.currentUser) {
        loadUserData();
        initializeNotifications();
        startPeriodicUpdates();
    }
    
    // Inicializar eventos globales
    initializeGlobalEvents();
    
    // Mostrar animaciones de entrada
    animatePageLoad();
    
    console.log('✅ Taskly inicializado correctamente');
}

// ===== GESTIÓN DE TOOLTIPS Y POPOVERS =====
function initializeTooltips() {
    // Inicializar todos los tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"], [title]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            delay: { show: 500, hide: 100 },
            placement: 'auto'
        });
    });
    
    console.log(`📝 ${tooltipList.length} tooltips inicializados`);
}

function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            trigger: 'hover focus',
            delay: { show: 300, hide: 100 }
        });
    });
    
    console.log(`💬 ${popoverList.length} popovers inicializados`);
}

function initializeModals() {
    // Configurar comportamiento de modales
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('show.bs.modal', function() {
            document.body.classList.add('modal-open-custom');
        });
        
        modal.addEventListener('hidden.bs.modal', function() {
            document.body.classList.remove('modal-open-custom');
            // Limpiar formularios en modales
            const forms = modal.querySelectorAll('form');
            forms.forEach(form => form.reset());
        });
    });
}

// ===== GESTIÓN DE TEMAS =====
function initializeTheme() {
    // Aplicar tema guardado
    applyTheme(currentTheme);
    
    // Escuchar cambios en preferencias del sistema
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            if (!localStorage.getItem('taskly-theme')) {
                applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }
}

function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(currentTheme);
    localStorage.setItem('taskly-theme', currentTheme);
    
    showNotification(`Tema ${currentTheme === 'dark' ? 'oscuro' : 'claro'} activado`, 'info');
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    currentTheme = theme;
    
    // Actualizar iconos de tema si existen
    const themeIcons = document.querySelectorAll('.theme-toggle i');
    themeIcons.forEach(icon => {
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    });
}

// ===== GESTIÓN DE CARGA Y LOADING =====
function showLoading(message = 'Cargando...') {
    if (isLoading) return;
    
    isLoading = true;
    let overlay = document.getElementById('loading-overlay');
    
    if (!overlay) {
        overlay = createLoadingOverlay();
        document.body.appendChild(overlay);
    }
    
    // Actualizar mensaje si se proporciona
    const loadingText = overlay.querySelector('.loading-text');
    if (loadingText) {
        loadingText.textContent = message;
    }
    
    overlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function hideLoading() {
    if (!isLoading) return;
    
    isLoading = false;
    const overlay = document.getElementById('loading-overlay');
    
    if (overlay) {
        overlay.style.display = 'none';
        document.body.style.overflow = '';
    }
}

function createLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="d-flex flex-column align-items-center">
            <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <div class="loading-text text-white fs-5">Cargando...</div>
        </div>
    `;
    return overlay;
}

// ===== SISTEMA DE NOTIFICACIONES =====
function showNotification(message, type = 'info', duration = 4000) {
    const notification = createNotificationElement(message, type);
    document.body.appendChild(notification);
    
    // Mostrar con animación
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Auto-remover
    setTimeout(() => {
        removeNotification(notification);
    }, duration);
    
    // Permitir cierre manual
    const closeBtn = notification.querySelector('.btn-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => removeNotification(notification));
    }
    
    console.log(`📢 Notificación: ${message} (${type})`);
}

function createNotificationElement(message, type) {
    const notification = document.createElement('div');
    const alertClass = type === 'error' ? 'danger' : type;
    const icon = getNotificationIcon(type);
    
    notification.className = `alert alert-${alertClass} alert-dismissible fade position-fixed notification-toast`;
    notification.style.cssText = `
        top: 20px; 
        right: 20px; 
        z-index: 9999; 
        min-width: 350px; 
        max-width: 400px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border: none;
        border-radius: 10px;
    `;
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="${icon} me-2 fs-5"></i>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close ms-2" aria-label="Cerrar"></button>
        </div>
    `;
    
    return notification;
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-triangle',
        'warning': 'fas fa-exclamation-circle',
        'info': 'fas fa-info-circle',
        'danger': 'fas fa-times-circle'
    };
    return icons[type] || icons.info;
}

function removeNotification(notification) {
    notification.classList.remove('show');
    notification.classList.add('fade-out');
    
    setTimeout(() => {
        if (notification && notification.parentNode) {
            notification.remove();
        }
    }, 300);
}

// ===== GESTIÓN DE DATOS DEL USUARIO =====
function loadUserData() {
    if (!window.TASKLY.currentUser) return;
    
    const user = window.TASKLY.currentUser;
    console.log(`👤 Usuario cargado: ${user.full_name} (${user.role})`);
    
    // Actualizar elementos de usuario en la interfaz
    updateUserInterface(user);
    
    // Cargar preferencias guardadas
    loadUserPreferences();
}

function updateUserInterface(user) {
    // Actualizar nombre en navbar
    const userNameElements = document.querySelectorAll('.user-name');
    userNameElements.forEach(el => el.textContent = user.full_name);
    
    // Actualizar role badges
    const roleElements = document.querySelectorAll('.user-role');
    roleElements.forEach(el => el.textContent = user.role);
    
    // Mostrar/ocultar elementos según rol
    if (user.role === 'Organizador') {
        document.querySelectorAll('.admin-only').forEach(el => el.style.display = '');
    } else {
        document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'none');
    }
}

function loadUserPreferences() {
    const preferences = JSON.parse(localStorage.getItem('taskly-preferences') || '{}');
    
    // Aplicar preferencias guardadas
    if (preferences.notifications !== undefined) {
        toggleNotifications(preferences.notifications);
    }
    
    if (preferences.autoSave !== undefined) {
        toggleAutoSave(preferences.autoSave);
    }
}

function saveUserPreference(key, value) {
    const preferences = JSON.parse(localStorage.getItem('taskly-preferences') || '{}');
    preferences[key] = value;
    localStorage.setItem('taskly-preferences', JSON.stringify(preferences));
}

// ===== NOTIFICACIONES DEL SISTEMA =====
function initializeNotifications() {
    if (!window.TASKLY.urls.notifications) return;
    
    loadNotifications();
    
    // Auto-refresh cada 5 minutos
    setInterval(loadNotifications, 5 * 60 * 1000);
}

function loadNotifications() {
    if (!window.TASKLY.currentUser) return;
    
    fetch(window.TASKLY.urls.notifications)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateNotificationsUI(data.notifications || []);
                notificationCount = data.count || 0;
                updateNotificationBadge();
            }
        })
        .catch(error => {
            console.warn('⚠️ Error cargando notificaciones:', error);
        });
}

function updateNotificationsUI(notifications) {
    const container = document.getElementById('notifications-container');
    if (!container) return;
    
    if (notifications.length === 0) {
        container.innerHTML = '<li><span class="dropdown-item-text text-muted">No hay notificaciones</span></li>';
        return;
    }
    
    let html = '';
    notifications.slice(0, 5).forEach(function(notif) {
        const urgencyClass = getUrgencyClass(notif.urgency);
        const icon = getUrgencyIcon(notif.urgency);
        
        html += `
            <li>
                <a class="dropdown-item py-2 notification-item" href="/events/${notif.event_id}/view">
                    <div class="d-flex align-items-start">
                        <i class="${icon} ${urgencyClass} me-2 mt-1"></i>
                        <div class="flex-grow-1">
                            <div class="fw-semibold">${escapeHtml(notif.title)}</div>
                            <small class="text-muted">${escapeHtml(notif.message)}</small>
                            <div class="text-muted" style="font-size: 0.7rem;">
                                ${formatNotificationTime(notif.event_date)}
                            </div>
                        </div>
                    </div>
                </a>
            </li>
        `;
    });
    
    container.innerHTML = html;
}

function getUrgencyClass(urgency) {
    const classes = {
        'urgent': 'text-danger',
        'warning': 'text-warning',
        'info': 'text-info'
    };
    return classes[urgency] || 'text-info';
}

function getUrgencyIcon(urgency) {
    const icons = {
        'urgent': 'fas fa-exclamation-triangle',
        'warning': 'fas fa-clock',
        'info': 'fas fa-info-circle'
    };
    return icons[urgency] || 'fas fa-bell';
}

function updateNotificationBadge() {
    const badge = document.getElementById('notification-count');
    if (!badge) return;
    
    if (notificationCount > 0) {
        badge.textContent = notificationCount > 99 ? '99+' : notificationCount;
        badge.style.display = 'inline';
    } else {
        badge.style.display = 'none';
    }
}

// ===== UTILIDADES GENERALES =====
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatNotificationTime(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = date - now;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
        if (diffHours === 0) {
            return 'En menos de 1 hora';
        } else if (diffHours > 0) {
            return `En ${diffHours} horas`;
        } else {
            return 'Pasado';
        }
    } else if (diffDays === 1) {
        return 'Mañana';
    } else if (diffDays > 1) {
        return `En ${diffDays} días`;
    } else {
        return 'Pasado';
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// ===== ANIMACIONES =====
function animatePageLoad() {
    // Animar elementos con animación de entrada
    const animatedElements = document.querySelectorAll('.animate-on-load');
    
    animatedElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.6s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

function animateCounter(element, target, duration = 1000) {
    const start = parseInt(element.textContent) || 0;
    const increment = (target - start) / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        element.textContent = Math.floor(current);
        
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        }
    }, 16);
}

function fadeIn(element, duration = 300) {
    element.style.opacity = '0';
    element.style.display = 'block';
    
    const start = performance.now();
    
    function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);
        
        element.style.opacity = progress;
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }
    
    requestAnimationFrame(animate);
}

function fadeOut(element, duration = 300) {
    const start = performance.now();
    const startOpacity = parseFloat(getComputedStyle(element).opacity);
    
    function animate(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);
        
        element.style.opacity = startOpacity * (1 - progress);
        
        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            element.style.display = 'none';
        }
    }
    
    requestAnimationFrame(animate);
}

// ===== EVENTOS GLOBALES =====
function initializeGlobalEvents() {
    // Atajos de teclado globales
    document.addEventListener('keydown', handleGlobalKeyboard);
    
    // Eventos de formularios
    initializeFormEvents();
    
    // Eventos de scroll
    initializeScrollEvents();
    
    // Eventos de resize
    window.addEventListener('resize', debounce(handleWindowResize, 250));
    
    // Eventos de conexión
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Prevenir envío accidental de formularios
    preventAccidentalSubmission();
}

function handleGlobalKeyboard(e) {
    // Ctrl/Cmd + K = Búsqueda rápida
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        focusSearchBox();
    }
    
    // Ctrl/Cmd + / = Mostrar atajos de teclado
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        showKeyboardShortcuts();
    }
    
    // Alt + T = Toggle tema
    if (e.altKey && e.key === 't') {
        e.preventDefault();
        toggleTheme();
    }
    
    // Escape = Cerrar modales/overlays
    if (e.key === 'Escape') {
        closeActiveOverlays();
    }
    
    // F1 = Ayuda
    if (e.key === 'F1') {
        e.preventDefault();
        showHelp();
    }
}

function initializeFormEvents() {
    // Auto-guardar formularios
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('input', debounce(() => autoSaveForm(form), 2000));
        });
    });
    
    // Validación en tiempo real
    const validatedForms = document.querySelectorAll('[data-real-time-validation]');
    validatedForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('input', debounce(() => validateField(input), 500));
        });
    });
    
    // Confirmación antes de salir de páginas con cambios
    trackFormChanges();
}

function initializeScrollEvents() {
    let ticking = false;
    
    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(() => {
                handleScroll();
                ticking = false;
            });
            ticking = true;
        }
    });
}

function handleScroll() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    // Navbar scroll effect
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (scrollTop > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
    
    // Lazy loading de imágenes
    lazyLoadImages();
    
    // Animaciones al hacer scroll
    animateOnScroll();
    
    // Botón back to top
    toggleBackToTop(scrollTop);
}

function handleWindowResize() {
    // Recalcular alturas de elementos
    recalculateElementHeights();
    
    // Actualizar gráficos si existen
    if (window.updateCharts) {
        window.updateCharts();
    }
    
    // Reorganizar elementos responsivos
    reorganizeResponsiveElements();
}

function handleOnline() {
    showNotification('Conexión restaurada', 'success', 3000);
    
    // Sincronizar datos pendientes
    syncPendingData();
}

function handleOffline() {
    showNotification('Sin conexión a internet', 'warning', 5000);
    
    // Cambiar a modo offline
    enableOfflineMode();
}

// ===== FUNCIONES DE UTILIDAD =====
function focusSearchBox() {
    const searchBox = document.querySelector('input[name="q"], .search-input, #search');
    if (searchBox) {
        searchBox.focus();
        searchBox.select();
    }
}

function showKeyboardShortcuts() {
    const shortcuts = [
        { keys: 'Ctrl + K', description: 'Búsqueda rápida' },
        { keys: 'Ctrl + /', description: 'Mostrar atajos' },
        { keys: 'Alt + T', description: 'Cambiar tema' },
        { keys: 'Escape', description: 'Cerrar modales' },
        { keys: 'F1', description: 'Ayuda' },
        { keys: 'Ctrl + N', description: 'Nuevo elemento' },
        { keys: 'Ctrl + S', description: 'Guardar' }
    ];
    
    let html = '<div class="keyboard-shortcuts"><h5>Atajos de Teclado</h5><ul class="list-unstyled">';
    shortcuts.forEach(shortcut => {
        html += `<li><kbd>${shortcut.keys}</kbd> - ${shortcut.description}</li>`;
    });
    html += '</ul></div>';
    
    showModal('Atajos de Teclado', html);
}

function closeActiveOverlays() {
    // Cerrar modales
    const activeModals = document.querySelectorAll('.modal.show');
    activeModals.forEach(modal => {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    });
    
    // Cerrar dropdowns
    const activeDropdowns = document.querySelectorAll('.dropdown-menu.show');
    activeDropdowns.forEach(dropdown => {
        const toggle = dropdown.previousElementSibling;
        if (toggle) {
            const dropdownInstance = bootstrap.Dropdown.getInstance(toggle);
            if (dropdownInstance) {
                dropdownInstance.hide();
            }
        }
    });
}

function showHelp() {
    window.open('/help', '_blank');
}

function autoSaveForm(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Guardar en localStorage
    const formId = form.id || 'auto-save-form';
    localStorage.setItem(`taskly-autosave-${formId}`, JSON.stringify(data));
    
    // Mostrar indicador de guardado
    showSaveIndicator(form);
}

function showSaveIndicator(form) {
    let indicator = form.querySelector('.save-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'save-indicator text-success small';
        indicator.innerHTML = '<i class="fas fa-check me-1"></i>Guardado automáticamente';
        form.appendChild(indicator);
    }
    
    indicator.style.opacity = '1';
    setTimeout(() => {
        indicator.style.opacity = '0';
    }, 2000);
}

function validateField(input) {
    const value = input.value.trim();
    const type = input.type;
    const required = input.hasAttribute('required');
    
    let isValid = true;
    let message = '';
    
    // Validaciones básicas
    if (required && !value) {
        isValid = false;
        message = 'Este campo es obligatorio';
    } else if (type === 'email' && value && !isValidEmail(value)) {
        isValid = false;
        message = 'Formato de email inválido';
    } else if (type === 'url' && value && !isValidUrl(value)) {
        isValid = false;
        message = 'Formato de URL inválido';
    } else if (input.hasAttribute('minlength') && value.length < parseInt(input.getAttribute('minlength'))) {
        isValid = false;
        message = `Mínimo ${input.getAttribute('minlength')} caracteres`;
    }
    
    // Mostrar/ocultar mensaje de error
    showFieldValidation(input, isValid, message);
    
    return isValid;
}

function showFieldValidation(input, isValid, message) {
    // Remover clases anteriores
    input.classList.remove('is-valid', 'is-invalid');
    
    // Remover mensaje anterior
    const existingFeedback = input.parentNode.querySelector('.invalid-feedback, .valid-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    if (!isValid) {
        input.classList.add('is-invalid');
        
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.textContent = message;
        input.parentNode.appendChild(feedback);
    } else if (input.value.trim()) {
        input.classList.add('is-valid');
    }
}

function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

function trackFormChanges() {
    const forms = document.querySelectorAll('form[data-warn-unsaved]');
    let hasUnsavedChanges = false;
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                hasUnsavedChanges = true;
            });
        });
        
        form.addEventListener('submit', () => {
            hasUnsavedChanges = false;
        });
    });
    
    // Advertir antes de salir
    window.addEventListener('beforeunload', (e) => {
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = '¿Estás seguro de salir? Tienes cambios sin guardar.';
        }
    });
}

function preventAccidentalSubmission() {
    // Prevenir doble envío de formularios
    document.addEventListener('submit', (e) => {
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        
        if (submitBtn && !submitBtn.disabled) {
            submitBtn.disabled = true;
            submitBtn.dataset.originalText = submitBtn.innerHTML;
            
            if (submitBtn.tagName === 'BUTTON') {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando...';
            }
            
            // Re-habilitar después de 5 segundos como fallback
            setTimeout(() => {
                submitBtn.disabled = false;
                if (submitBtn.dataset.originalText) {
                    submitBtn.innerHTML = submitBtn.dataset.originalText;
                }
            }, 5000);
        }
    });
}

// ===== FUNCIONES DE SCROLL =====
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    
    images.forEach(img => {
        if (isElementInViewport(img)) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            img.classList.add('loaded');
        }
    });
}

function animateOnScroll() {
    const elements = document.querySelectorAll('.animate-on-scroll');
    
    elements.forEach(element => {
        if (isElementInViewport(element) && !element.classList.contains('animated')) {
            element.classList.add('animated', 'animate-fade-in');
        }
    });
}

function toggleBackToTop(scrollTop) {
    let backToTopBtn = document.getElementById('back-to-top');
    
    if (!backToTopBtn) {
        backToTopBtn = createBackToTopButton();
        document.body.appendChild(backToTopBtn);
    }
    
    if (scrollTop > 300) {
        backToTopBtn.style.display = 'block';
        setTimeout(() => backToTopBtn.style.opacity = '1', 10);
    } else {
        backToTopBtn.style.opacity = '0';
        setTimeout(() => backToTopBtn.style.display = 'none', 300);
    }
}

function createBackToTopButton() {
    const button = document.createElement('button');
    button.id = 'back-to-top';
    button.innerHTML = '<i class="fas fa-chevron-up"></i>';
    button.className = 'btn btn-primary';
    button.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 20px;
        z-index: 1000;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: none;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    button.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    
    return button;
}

function isElementInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// ===== FUNCIONES DE UTILIDAD ADICIONALES =====
function recalculateElementHeights() {
    // Recalcular altura de elementos que dependen del viewport
    const fullHeightElements = document.querySelectorAll('.full-height');
    fullHeightElements.forEach(element => {
        element.style.height = window.innerHeight + 'px';
    });
}

function reorganizeResponsiveElements() {
    const width = window.innerWidth;
    
    // Reorganizar elementos según el ancho de pantalla
    if (width < 768) {
        // Móvil
        document.body.classList.add('mobile-view');
        document.body.classList.remove('desktop-view');
    } else {
        // Desktop
        document.body.classList.add('desktop-view');
        document.body.classList.remove('mobile-view');
    }
}

function syncPendingData() {
    // Implementar sincronización de datos offline
    const pendingData = JSON.parse(localStorage.getItem('taskly-pending-sync') || '[]');
    
    if (pendingData.length > 0) {
        console.log(`🔄 Sincronizando ${pendingData.length} elementos pendientes...`);
        
        // Procesar datos pendientes
        pendingData.forEach(async (item, index) => {
            try {
                await syncDataItem(item);
                // Remover elemento sincronizado
                pendingData.splice(index, 1);
            } catch (error) {
                console.error('Error sincronizando elemento:', error);
            }
        });
        
        // Actualizar storage
        localStorage.setItem('taskly-pending-sync', JSON.stringify(pendingData));
    }
}

function enableOfflineMode() {
    document.body.classList.add('offline-mode');
    
    // Deshabilitar funciones que requieren conexión
    const onlineOnlyElements = document.querySelectorAll('.online-only');
    onlineOnlyElements.forEach(element => {
        element.style.opacity = '0.5';
        element.style.pointerEvents = 'none';
    });
}

async function syncDataItem(item) {
    // Implementar sincronización individual de elementos
    const response = await fetch(item.url, {
        method: item.method,
        headers: item.headers,
        body: item.body
    });
    
    if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
}

function showModal(title, content, actions = []) {
    // Crear modal dinámico
    const modalId = 'dynamic-modal-' + Date.now();
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = modalId;
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-labelledby', modalId + '-title');
    modal.setAttribute('aria-hidden', 'true');
    
    // Construir HTML del modal
    let actionsHtml = '';
    if (actions.length > 0) {
        actionsHtml = '<div class="modal-footer">';
        actions.forEach(action => {
            actionsHtml += `<button type="button" class="btn btn-${action.type || 'secondary'}" 
                           onclick="${action.onclick || ''}" 
                           ${action.dismiss ? 'data-bs-dismiss="modal"' : ''}>
                           ${action.text}
                           </button>`;
        });
        actionsHtml += '</div>';
    } else {
        actionsHtml = `
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
            </div>
        `;
    }
    
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="${modalId}-title">${escapeHtml(title)}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                ${actionsHtml}
            </div>
        </div>
    `;
    
    // Agregar al DOM
    document.body.appendChild(modal);
    
    // Mostrar modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    // Limpiar cuando se cierre
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
    
    return modalInstance;
}

// ===== VALIDACIÓN DE FORMULARIOS =====
function validateField(input) {
    const value = input.value.trim();
    const type = input.type;
    const required = input.hasAttribute('required');
    const minLength = input.getAttribute('minlength');
    const maxLength = input.getAttribute('maxlength');
    const pattern = input.getAttribute('pattern');
    
    let isValid = true;
    let message = '';
    
    // Validaciones básicas
    if (required && !value) {
        isValid = false;
        message = 'Este campo es obligatorio';
    } else if (value) {
        // Solo validar formato si hay valor
        if (type === 'email' && !isValidEmail(value)) {
            isValid = false;
            message = 'Formato de email inválido';
        } else if (type === 'url' && !isValidUrl(value)) {
            isValid = false;
            message = 'Formato de URL inválido';
        } else if (minLength && value.length < parseInt(minLength)) {
            isValid = false;
            message = `Mínimo ${minLength} caracteres`;
        } else if (maxLength && value.length > parseInt(maxLength)) {
            isValid = false;
            message = `Máximo ${maxLength} caracteres`;
        } else if (pattern && !new RegExp(pattern).test(value)) {
            isValid = false;
            message = 'Formato inválido';
        }
    }
    
    // Validaciones personalizadas
    if (isValid && input.dataset.customValidation) {
        const result = customValidation(input, value);
        isValid = result.isValid;
        message = result.message;
    }
    
    // Mostrar/ocultar mensaje de error
    showFieldValidation(input, isValid, message);
    
    return isValid;
}

function showFieldValidation(input, isValid, message) {
    // Remover clases anteriores
    input.classList.remove('is-valid', 'is-invalid');
    
    // Remover mensaje anterior
    const existingFeedback = input.parentNode.querySelector('.invalid-feedback, .valid-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    
    if (!isValid) {
        input.classList.add('is-invalid');
        
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        feedback.innerHTML = `<i class="fas fa-exclamation-circle me-1"></i>${message}`;
        input.parentNode.appendChild(feedback);
    } else if (input.value.trim()) {
        input.classList.add('is-valid');
        
        const feedback = document.createElement('div');
        feedback.className = 'valid-feedback';
        feedback.innerHTML = `<i class="fas fa-check-circle me-1"></i>Válido`;
        input.parentNode.appendChild(feedback);
    }
}

function customValidation(input, value) {
    const validationType = input.dataset.customValidation;
    
    switch (validationType) {
        case 'username':
            return validateUsername(value);
        case 'strong-password':
            return validateStrongPassword(value);
        case 'confirm-password':
            return validateConfirmPassword(input, value);
        case 'date-future':
            return validateFutureDate(value);
        case 'date-past':
            return validatePastDate(value);
        default:
            return { isValid: true, message: '' };
    }
}

function validateUsername(value) {
    const regex = /^[a-zA-Z0-9_]{3,20}$/;
    if (!regex.test(value)) {
        return {
            isValid: false,
            message: 'El usuario debe tener 3-20 caracteres (letras, números y _)'
        };
    }
    return { isValid: true, message: '' };
}

function validateStrongPassword(value) {
    const checks = [
        { regex: /.{8,}/, message: 'al menos 8 caracteres' },
        { regex: /[A-Z]/, message: 'una letra mayúscula' },
        { regex: /[a-z]/, message: 'una letra minúscula' },
        { regex: /[0-9]/, message: 'un número' },
        { regex: /[^A-Za-z0-9]/, message: 'un carácter especial' }
    ];
    
    const failed = checks.filter(check => !check.regex.test(value));
    
    if (failed.length > 0) {
        return {
            isValid: false,
            message: `La contraseña debe tener ${failed.map(f => f.message).join(', ')}`
        };
    }
    
    return { isValid: true, message: '' };
}

function validateConfirmPassword(input, value) {
    const passwordField = document.querySelector(input.dataset.confirmTarget || 'input[name="password"]');
    
    if (!passwordField) {
        return { isValid: false, message: 'Campo de contraseña no encontrado' };
    }
    
    if (value !== passwordField.value) {
        return { isValid: false, message: 'Las contraseñas no coinciden' };
    }
    
    return { isValid: true, message: '' };
}

function validateFutureDate(value) {
    const inputDate = new Date(value);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (inputDate <= today) {
        return {
            isValid: false,
            message: 'La fecha debe ser posterior a hoy'
        };
    }
    
    return { isValid: true, message: '' };
}

function validatePastDate(value) {
    const inputDate = new Date(value);
    const today = new Date();
    
    if (inputDate >= today) {
        return {
            isValid: false,
            message: 'La fecha debe ser anterior a hoy'
        };
    }
    
    return { isValid: true, message: '' };
}

function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// ===== AUTO-COMPLETE Y SUGERENCIAS =====
function initializeAutoComplete() {
    const autoCompleteFields = document.querySelectorAll('[data-autocomplete]');
    
    autoCompleteFields.forEach(field => {
        setupAutoComplete(field);
    });
}

function setupAutoComplete(field) {
    const source = field.dataset.autocomplete;
    let suggestions = [];
    
    // Cargar sugerencias
    if (source === 'local') {
        suggestions = getLocalSuggestions(field);
    } else if (source.startsWith('http')) {
        loadRemoteSuggestions(field, source);
    }
    
    // Crear contenedor de sugerencias
    const suggestionsContainer = createSuggestionsContainer(field);
    
    // Eventos de autocompletado
    field.addEventListener('input', debounce((e) => {
        showSuggestions(field, suggestionsContainer, e.target.value);
    }, 300));
    
    field.addEventListener('blur', () => {
        setTimeout(() => hideSuggestions(suggestionsContainer), 200);
    });
    
    field.addEventListener('keydown', (e) => {
        handleAutoCompleteNavigation(e, suggestionsContainer);
    });
}

function createSuggestionsContainer(field) {
    const container = document.createElement('div');
    container.className = 'autocomplete-suggestions';
    container.style.cssText = `
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border: 1px solid #ddd;
        border-top: none;
        border-radius: 0 0 8px 8px;
        max-height: 200px;
        overflow-y: auto;
        z-index: 1000;
        display: none;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    `;
    
    // Hacer el campo padre relativo
    field.parentNode.style.position = 'relative';
    field.parentNode.appendChild(container);
    
    return container;
}

function showSuggestions(field, container, query) {
    if (!query || query.length < 2) {
        hideSuggestions(container);
        return;
    }
    
    const suggestions = getSuggestions(field, query);
    
    if (suggestions.length === 0) {
        hideSuggestions(container);
        return;
    }
    
    let html = '';
    suggestions.forEach((suggestion, index) => {
        html += `
            <div class="autocomplete-item" 
                 data-value="${escapeHtml(suggestion.value)}"
                 data-index="${index}"
                 style="padding: 0.5rem; cursor: pointer; ${index === 0 ? 'background: #f8f9fa;' : ''}">
                <div class="fw-semibold">${highlightMatch(suggestion.label, query)}</div>
                ${suggestion.description ? `<small class="text-muted">${suggestion.description}</small>` : ''}
            </div>
        `;
    });
    
    container.innerHTML = html;
    container.style.display = 'block';
    
    // Eventos de clic en sugerencias
    container.querySelectorAll('.autocomplete-item').forEach(item => {
        item.addEventListener('click', () => {
            field.value = item.dataset.value;
            hideSuggestions(container);
            field.dispatchEvent(new Event('input', { bubbles: true }));
        });
        
        item.addEventListener('mouseenter', () => {
            container.querySelectorAll('.autocomplete-item').forEach(i => i.style.background = '');
            item.style.background = '#f8f9fa';
        });
    });
}

function hideSuggestions(container) {
    container.style.display = 'none';
}

function highlightMatch(text, query) {
    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function getSuggestions(field, query) {
    // Implementar lógica de sugerencias según el tipo de campo
    const type = field.dataset.autocompleteType;
    
    switch (type) {
        case 'tags':
            return getTagSuggestions(query);
        case 'users':
            return getUserSuggestions(query);
        case 'locations':
            return getLocationSuggestions(query);
        default:
            return getDefaultSuggestions(field, query);
    }
}

function getTagSuggestions(query) {
    const commonTags = [
        { value: 'trabajo', label: 'Trabajo', description: 'Tareas relacionadas con el trabajo' },
        { value: 'personal', label: 'Personal', description: 'Tareas personales' },
        { value: 'urgente', label: 'Urgente', description: 'Tareas que requieren atención inmediata' },
        { value: 'proyecto', label: 'Proyecto', description: 'Tareas de proyecto' },
        { value: 'reunion', label: 'Reunión', description: 'Eventos de reunión' },
        { value: 'importante', label: 'Importante', description: 'Elementos importantes' }
    ];
    
    return commonTags.filter(tag => 
        tag.label.toLowerCase().includes(query.toLowerCase()) ||
        tag.value.toLowerCase().includes(query.toLowerCase())
    );
}

function getUserSuggestions(query) {
    // En una implementación real, esto vendría del servidor
    const users = JSON.parse(localStorage.getItem('taskly-users-cache') || '[]');
    
    return users.filter(user => 
        user.name.toLowerCase().includes(query.toLowerCase()) ||
        user.username.toLowerCase().includes(query.toLowerCase())
    ).map(user => ({
        value: user.username,
        label: user.name,
        description: `@${user.username}`
    }));
}

function getLocationSuggestions(query) {
    const commonLocations = [
        { value: 'oficina', label: 'Oficina', description: 'Oficina principal' },
        { value: 'casa', label: 'Casa', description: 'Trabajo desde casa' },
        { value: 'sala-reuniones', label: 'Sala de Reuniones', description: 'Sala de reuniones principal' },
        { value: 'online', label: 'Online', description: 'Reunión virtual' }
    ];
    
    return commonLocations.filter(location => 
        location.label.toLowerCase().includes(query.toLowerCase())
    );
}

function getDefaultSuggestions(field, query) {
    // Obtener sugerencias del historial local
    const fieldName = field.name || field.id;
    const history = JSON.parse(localStorage.getItem(`taskly-history-${fieldName}`) || '[]');
    
    return history
        .filter(item => item.toLowerCase().includes(query.toLowerCase()))
        .slice(0, 5)
        .map(item => ({ value: item, label: item }));
}

// ===== GESTIÓN DE HISTORIAL =====
function saveToHistory(fieldName, value) {
    if (!value || value.length < 3) return;
    
    const history = JSON.parse(localStorage.getItem(`taskly-history-${fieldName}`) || '[]');
    
    // Agregar al inicio y remover duplicados
    const newHistory = [value, ...history.filter(item => item !== value)].slice(0, 10);
    
    localStorage.setItem(`taskly-history-${fieldName}`, JSON.stringify(newHistory));
}

// ===== FUNCIONES DE SCROLL ADICIONALES =====
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]:not(.loaded)');
    
    images.forEach(img => {
        if (isElementInViewport(img)) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            img.classList.add('loaded');
            
            // Efecto de fade in
            img.style.opacity = '0';
            img.onload = () => {
                img.style.transition = 'opacity 0.3s ease';
                img.style.opacity = '1';
            };
        }
    });
}

function animateOnScroll() {
    const elements = document.querySelectorAll('.animate-on-scroll:not(.animated)');
    
    elements.forEach(element => {
        if (isElementInViewport(element)) {
            element.classList.add('animated');
            
            const animation = element.dataset.animation || 'fadeInUp';
            element.style.animationName = animation;
            element.style.animationDuration = '0.6s';
            element.style.animationFillMode = 'both';
        }
    });
}

function handleInfiniteScroll(scrollTop) {
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = document.documentElement.clientHeight;
    
    // Si estamos cerca del final (dentro de 100px)
    if (scrollTop + clientHeight >= scrollHeight - 100) {
        const infiniteContainer = document.querySelector('[data-infinite-scroll]');
        if (infiniteContainer && !infiniteContainer.dataset.loading) {
            loadMoreContent(infiniteContainer);
        }
    }
}

function loadMoreContent(container) {
    container.dataset.loading = 'true';
    
    // Mostrar indicador de carga
    const loader = document.createElement('div');
    loader.className = 'text-center py-3 infinite-loader';
    loader.innerHTML = `
        <div class="d-flex align-items-center justify-content-center">
            <div class="spinner-border spinner-border-sm me-2"></div>
            <span>Cargando más contenido...</span>
        </div>
    `;
    container.appendChild(loader);
    
    // Obtener datos para cargar más
    const loadUrl = container.dataset.loadUrl;
    const currentPage = parseInt(container.dataset.currentPage || '1');
    const nextPage = currentPage + 1;
    
    if (loadUrl) {
        // Cargar contenido real vía AJAX
        fetch(`${loadUrl}?page=${nextPage}`)
            .then(response => response.json())
            .then(data => {
                loader.remove();
                
                if (data.success && data.content) {
                    // Agregar nuevo contenido
                    container.insertAdjacentHTML('beforeend', data.content);
                    container.dataset.currentPage = nextPage;
                    
                    // Inicializar nuevos elementos
                    initializeNewElements(container.lastElementChild);
                    
                    if (!data.hasMore) {
                        // No hay más contenido
                        showEndOfContent(container);
                    }
                } else {
                    showLoadError(container);
                }
                
                container.dataset.loading = 'false';
            })
            .catch(error => {
                console.error('Error cargando contenido:', error);
                loader.remove();
                showLoadError(container);
                container.dataset.loading = 'false';
            });
    } else {
        // Simular carga para demo
        setTimeout(() => {
            loader.remove();
            container.dataset.loading = 'false';
            showEndOfContent(container);
        }, 1500);
    }
}

function initializeNewElements(container) {
    // Reinicializar tooltips en nuevos elementos
    const newTooltips = container.querySelectorAll('[data-bs-toggle="tooltip"], [title]');
    newTooltips.forEach(element => {
        new bootstrap.Tooltip(element);
    });
    
    // Reinicializar otros componentes si es necesario
    const newPopovers = container.querySelectorAll('[data-bs-toggle="popover"]');
    newPopovers.forEach(element => {
        new bootstrap.Popover(element);
    });
}

function showEndOfContent(container) {
    const endMessage = document.createElement('div');
    endMessage.className = 'text-center py-4 text-muted end-of-content';
    endMessage.innerHTML = `
        <i class="fas fa-check-circle fa-2x mb-2"></i>
        <p class="mb-0">Has visto todo el contenido disponible</p>
    `;
    container.appendChild(endMessage);
}

function showLoadError(container) {
    const errorMessage = document.createElement('div');
    errorMessage.className = 'text-center py-3 text-danger load-error';
    errorMessage.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>
        Error cargando contenido. 
        <button class="btn btn-link btn-sm p-0" onclick="retryLoadMore(this)">Reintentar</button>
    `;
    container.appendChild(errorMessage);
}

function retryLoadMore(button) {
    const container = button.closest('[data-infinite-scroll]');
    const errorMessage = button.closest('.load-error');
    
    if (container && errorMessage) {
        errorMessage.remove();
        loadMoreContent(container);
    }
}

// ===== GESTIÓN DE PESTAÑAS Y NAVEGACIÓN =====
function initializeTabNavigation() {
    // Recordar pestaña activa
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', (e) => {
            const tabId = e.target.getAttribute('href');
            localStorage.setItem('taskly-active-tab', tabId);
        });
    });
    
    // Restaurar pestaña activa
    const activeTab = localStorage.getItem('taskly-active-tab');
    if (activeTab) {
        const tabElement = document.querySelector(`[href="${activeTab}"]`);
        if (tabElement) {
            const tab = new bootstrap.Tab(tabElement);
            tab.show();
        }
    }
}

// ===== SISTEMA DE CACHÉ =====
function cacheData(key, data, expirationMinutes = 60) {
    const cacheObject = {
        data: data,
        timestamp: Date.now(),
        expiration: expirationMinutes * 60 * 1000
    };
    
    try {
        localStorage.setItem(`taskly-cache-${key}`, JSON.stringify(cacheObject));
    } catch (error) {
        console.warn('Error guardando en caché:', error);
    }
}

function getCachedData(key) {
    try {
        const cached = localStorage.getItem(`taskly-cache-${key}`);
        if (!cached) return null;
        
        const cacheObject = JSON.parse(cached);
        const now = Date.now();
        
        // Verificar si ha expirado
        if (now - cacheObject.timestamp > cacheObject.expiration) {
            localStorage.removeItem(`taskly-cache-${key}`);
            return null;
        }
        
        return cacheObject.data;
    } catch (error) {
        console.warn('Error leyendo caché:', error);
        return null;
    }
}

function clearCache(pattern = null) {
    const keys = Object.keys(localStorage);
    
    keys.forEach(key => {
        if (key.startsWith('taskly-cache-')) {
            if (!pattern || key.includes(pattern)) {
                localStorage.removeItem(key);
            }
        }
    });
    
    console.log('🗑️ Caché limpiado');
}

// ===== GESTIÓN DE ESTADO DE LA APLICACIÓN =====
const AppState = {
    data: {},
    
    set(key, value) {
        this.data[key] = value;
        this.notifySubscribers(key, value);
    },
    
    get(key) {
        return this.data[key];
    },
    
    subscribers: {},
    
    subscribe(key, callback) {
        if (!this.subscribers[key]) {
            this.subscribers[key] = [];
        }
        this.subscribers[key].push(callback);
        
        // Llamar inmediatamente si ya hay datos
        if (this.data[key] !== undefined) {
            callback(this.data[key]);
        }
    },
    
    unsubscribe(key, callback) {
        if (this.subscribers[key]) {
            this.subscribers[key] = this.subscribers[key].filter(cb => cb !== callback);
        }
    },
    
    notifySubscribers(key, value) {
        if (this.subscribers[key]) {
            this.subscribers[key].forEach(callback => {
                try {
                    callback(value);
                } catch (error) {
                    console.error('Error en callback de estado:', error);
                }
            });
        }
    }
};

// ===== UTILIDADES DE FECHA Y TIEMPO =====
function formatDate(date, format = 'relative') {
    if (!date) return '';
    
    const dateObj = new Date(date);
    const now = new Date();
    
    switch (format) {
        case 'relative':
            return getRelativeTime(dateObj, now);
        case 'short':
            return dateObj.toLocaleDateString('es-ES', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        case 'long':
            return dateObj.toLocaleDateString('es-ES', {
                weekday: 'long',
                day: 'numeric',
                month: 'long',
                year: 'numeric'
            });
        case 'time':
            return dateObj.toLocaleTimeString('es-ES', {
                hour: '2-digit',
                minute: '2-digit'
            });
        case 'datetime':
            return dateObj.toLocaleString('es-ES', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        default:
            return dateObj.toLocaleDateString('es-ES');
    }
}

function getRelativeTime(date, now = new Date()) {
    const diffMs = now - date;
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSeconds < 60) {
        return 'Hace un momento';
    } else if (diffMinutes < 60) {
        return `Hace ${diffMinutes} minuto${diffMinutes !== 1 ? 's' : ''}`;
    } else if (diffHours < 24) {
        return `Hace ${diffHours} hora${diffHours !== 1 ? 's' : ''}`;
    } else if (diffDays < 7) {
        return `Hace ${diffDays} día${diffDays !== 1 ? 's' : ''}`;
    } else if (diffDays < 30) {
        const weeks = Math.floor(diffDays / 7);
        return `Hace ${weeks} semana${weeks !== 1 ? 's' : ''}`;
    } else if (diffDays < 365) {
        const months = Math.floor(diffDays / 30);
        return `Hace ${months} mes${months !== 1 ? 'es' : ''}`;
    } else {
        const years = Math.floor(diffDays / 365);
        return `Hace ${years} año${years !== 1 ? 's' : ''}`;
    }
}

function getTimeUntil(date) {
    const now = new Date();
    const diffMs = date - now;
    
    if (diffMs <= 0) {
        return 'Pasado';
    }
    
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) {
        return `En ${diffDays} día${diffDays !== 1 ? 's' : ''}`;
    } else if (diffHours > 0) {
        return `En ${diffHours} hora${diffHours !== 1 ? 's' : ''}`;
    } else if (diffMinutes > 0) {
        return `En ${diffMinutes} minuto${diffMinutes !== 1 ? 's' : ''}`;
    } else {
        return 'En unos momentos';
    }
}

// ===== UTILIDADES DE PERFORMANCE =====
function measurePerformance(name, fn) {
    const start = performance.now();
    const result = fn();
    const end = performance.now();
    
    console.log(`⏱️ ${name}: ${(end - start).toFixed(2)}ms`);
    return result;
}

function preloadImage(src) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = src;
    });
}

function preloadImages(urls) {
    return Promise.all(urls.map(url => preloadImage(url)));
}

// ===== GESTIÓN DE ERRORES GLOBALES =====
function setupErrorHandling() {
    // Manejar errores JavaScript no capturados
    window.addEventListener('error', (event) => {
        console.error('Error JavaScript:', event.error);
        
        // En desarrollo, mostrar error; en producción, solo registrar
        if (window.location.hostname === 'localhost') {
            showNotification(`Error: ${event.error.message}`, 'error', 8000);
        }
        
        // Enviar error a servicio de logging (si está configurado)
        logError({
            type: 'javascript',
            message: event.error.message,
            stack: event.error.stack,
            url: window.location.href,
            timestamp: new Date().toISOString()
        });
    });
    
    // Manejar promesas rechazadas no capturadas
    window.addEventListener('unhandledrejection', (event) => {
        console.error('Promise rechazada:', event.reason);
        
        if (window.location.hostname === 'localhost') {
            showNotification(`Error de promesa: ${event.reason}`, 'error', 8000);
        }
        
        logError({
            type: 'promise',
            message: event.reason.toString(),
            url: window.location.href,
            timestamp: new Date().toISOString()
        });
    });
}

function logError(errorData) {
    // Guardar en localStorage para envío posterior
    const errors = JSON.parse(localStorage.getItem('taskly-errors') || '[]');
    errors.push(errorData);
    
    // Mantener solo los últimos 50 errores
    if (errors.length > 50) {
        errors.splice(0, errors.length - 50);
    }
    
    localStorage.setItem('taskly-errors', JSON.stringify(errors));
    
    // En producción, enviar al servidor
    if (window.location.hostname !== 'localhost') {
        sendErrorToServer(errorData);
    }
}

function sendErrorToServer(errorData) {
    fetch('/api/errors', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorData)
    }).catch(error => {
        console.warn('No se pudo enviar error al servidor:', error);
    });
}

// ===== FUNCIONES DE UTILIDAD FINAL =====
function isElementInViewport(element, threshold = 0) {
    const rect = element.getBoundingClientRect();
    const windowHeight = window.innerHeight || document.documentElement.clientHeight;
    const windowWidth = window.innerWidth || document.documentElement.clientWidth;
    
    return (
        rect.top >= -threshold &&
        rect.left >= -threshold &&
        rect.bottom <= windowHeight + threshold &&
        rect.right <= windowWidth + threshold
    );
}

function pausePeriodicUpdates() {
    if (window.updateIntervals) {
        window.updateIntervals.forEach(interval => clearInterval(interval));
        window.updateIntervals = [];
    }
}

function resumePeriodicUpdates() {
    startPeriodicUpdates();
}

function enableOfflineMode() {
    document.body.classList.add('offline-mode');
    
    // Mostrar indicador de modo offline
    let offlineIndicator = document.getElementById('offline-indicator');
    if (!offlineIndicator) {
        offlineIndicator = document.createElement('div');
        offlineIndicator.id = 'offline-indicator';
        offlineIndicator.className = 'alert alert-warning position-fixed';
        offlineIndicator.style.cssText = 'top: 0; left: 0; right: 0; z-index: 9999; margin: 0; border-radius: 0;';
        offlineIndicator.innerHTML = `
            <div class="container text-center">
                <i class="fas fa-wifi-slash me-2"></i>
                Modo offline activado. Algunos funciones pueden estar limitadas.
            </div>
        `;
        document.body.insertBefore(offlineIndicator, document.body.firstChild);
    }
}

// ===== INICIALIZACIÓN FINAL =====
// Configurar manejo de errores
setupErrorHandling();

// Inicializar cuando el DOM esté completamente cargado
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}

// Exportar funciones globales para uso en otros archivos
window.TasklyJS = {
    showNotification,
    showLoading,
    hideLoading,
    showModal,
    formatDate,
    getRelativeTime,
    cacheData,
    getCachedData,
    clearCache,
    AppState,
    validateField,
    debounce,
    throttle,
    isElementInViewport,
    measurePerformance
};

console.log('📚 Taskly JavaScript cargado correctamente');