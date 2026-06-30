"""
Admin routes: users, employees, departments management.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from app.utils.decorators import admin_required
from app.utils.helpers import log_audit, get_client_ip

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users')
@admin_required
def users():
    """Manage system users."""
    all_users = User.get_all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    """Create new user."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', '')

        if not all([username, email, password, role]):
            flash('All fields are required.', 'danger')
            return render_template('admin/user_form.html', user=None)

        if User.get_by_username(username):
            flash('Username already exists.', 'danger')
            return render_template('admin/user_form.html', user=None)

        if User.get_by_email(email):
            flash('Email already exists.', 'danger')
            return render_template('admin/user_form.html', user=None)

        user_id = User.create(username, email, password, role)
        log_audit(current_user.id, 'user_created', 'user', user_id,
                  username, get_client_ip(request))
        flash('User created successfully.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', user=None)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit existing user."""
    user = User.get_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.users'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        role = request.form.get('role', '')
        is_active = 1 if request.form.get('is_active') == 'on' else 0
        password = request.form.get('password', '')

        User.update(user_id, username, email, role, is_active)
        if password:
            User.update_password(user_id, password)

        log_audit(current_user.id, 'user_updated', 'user', user_id,
                  username, get_client_ip(request))
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', user=user)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Deactivate user."""
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    User.delete(user_id)
    log_audit(current_user.id, 'user_deactivated', 'user', user_id,
              None, get_client_ip(request))
    flash('User deactivated.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/employees')
@admin_required
def employees():
    """Manage employees."""
    all_employees = Employee.get_all(active_only=False)
    return render_template('admin/employees.html', employees=all_employees)


@admin_bp.route('/employees/create', methods=['GET', 'POST'])
@admin_required
def create_employee():
    """Create employee record."""
    departments = Department.get_all()
    users = [u for u in User.get_all() if u.role in ('employee', 'admin')]

    if request.method == 'POST':
        data = {
            'user_id': request.form.get('user_id') or None,
            'department_id': request.form.get('department_id', type=int),
            'employee_code': request.form.get('employee_code', '').strip(),
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'email': request.form.get('email', '').strip(),
            'designation': request.form.get('designation', '').strip(),
        }
        if data['user_id']:
            data['user_id'] = int(data['user_id'])

        if not all([data['department_id'], data['employee_code'],
                    data['first_name'], data['last_name']]):
            flash('Required fields missing.', 'danger')
            return render_template('admin/employee_form.html',
                                   employee=None, departments=departments, users=users)

        emp_id = Employee.create(data)
        log_audit(current_user.id, 'employee_created', 'employee', emp_id,
                  data['employee_code'], get_client_ip(request))
        flash('Employee created.', 'success')
        return redirect(url_for('admin.employees'))

    return render_template('admin/employee_form.html',
                           employee=None, departments=departments, users=users)


@admin_bp.route('/employees/<int:emp_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_employee(emp_id):
    """Edit employee."""
    employee = Employee.get_by_id(emp_id)
    if not employee:
        flash('Employee not found.', 'danger')
        return redirect(url_for('admin.employees'))

    departments = Department.get_all()
    users = User.get_all()

    if request.method == 'POST':
        data = {
            'user_id': request.form.get('user_id') or None,
            'department_id': request.form.get('department_id', type=int),
            'employee_code': request.form.get('employee_code', '').strip(),
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'email': request.form.get('email', '').strip(),
            'designation': request.form.get('designation', '').strip(),
            'is_active': 1 if request.form.get('is_active') == 'on' else 0,
        }
        if data['user_id']:
            data['user_id'] = int(data['user_id'])

        Employee.update(emp_id, data)
        flash('Employee updated.', 'success')
        return redirect(url_for('admin.employees'))

    return render_template('admin/employee_form.html',
                           employee=employee, departments=departments, users=users)


@admin_bp.route('/departments')
@admin_required
def departments():
    """Manage departments."""
    depts = Department.get_all(active_only=False)
    return render_template('admin/departments.html', departments=depts)


@admin_bp.route('/departments/create', methods=['POST'])
@admin_required
def create_department():
    """Create department."""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if not name:
        flash('Department name is required.', 'danger')
    else:
        try:
            Department.create(name, description)
            flash('Department created.', 'success')
        except Exception:
            flash('Department name may already exist.', 'danger')
    return redirect(url_for('admin.departments'))


@admin_bp.route('/departments/<int:dept_id>/edit', methods=['POST'])
@admin_required
def edit_department(dept_id):
    """Update department."""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    is_active = 1 if request.form.get('is_active') == 'on' else 0
    Department.update(dept_id, name, description, is_active)
    flash('Department updated.', 'success')
    return redirect(url_for('admin.departments'))
