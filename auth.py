"""
Authentication routes: login, logout, profile.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.utils.helpers import log_audit, get_client_ip

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login for admin, employee, and receptionist."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')

        user = User.get_by_username(username)
        if user and User.verify_password(user, password):
            login_user(user, remember=remember)
            User.update_last_login(user.id)
            log_audit(user.id, 'login', 'user', user.id,
                      f'Role: {user.role}', get_client_ip(request))

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))

        flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out current user."""
    log_audit(current_user.id, 'logout', 'user', current_user.id,
              None, get_client_ip(request))
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    """View user profile."""
    from app.models.employee import Employee
    employee = Employee.get_by_user_id(current_user.id)
    return render_template('profile.html', employee=employee)
