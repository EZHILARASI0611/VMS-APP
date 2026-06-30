"""
Role-based access control decorators.
"""
from functools import wraps
from flask import abort, flash, redirect, url_for, request, jsonify
from flask_login import current_user


def role_required(*roles):
    """Restrict route to specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Authentication required'}), 401
                return redirect(url_for('auth.login', next=request.url))
            if current_user.role not in roles:
                if request.path.startswith('/api/'):
                    return jsonify({'success': False, 'message': 'Access denied'}), 403
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Shortcut for admin-only routes."""
    return role_required('admin')(f)


def receptionist_required(f):
    """Admin or receptionist access."""
    return role_required('admin', 'receptionist')(f)


def employee_required(f):
    """Admin or employee access."""
    return role_required('admin', 'employee')(f)
