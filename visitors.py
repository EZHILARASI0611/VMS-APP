"""
Visitor management routes: registration, check-in/out, tracking, QR pass.
"""
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request,
    send_file, current_app, jsonify
)
from flask_login import login_required, current_user
from app.models.visitor import Visitor, VisitorApproval
from app.models.employee import Employee
from app.models.department import Department
from app.utils.decorators import role_required, receptionist_required
from app.utils.helpers import (
    save_upload, generate_visitor_code, generate_badge_number,
    log_audit, get_client_ip
)
from app.utils.qr_generator import generate_visitor_qr
import os

visitors_bp = Blueprint('visitors', __name__, url_prefix='/visitors')


@visitors_bp.route('/')
@login_required
def list_visitors():
    """List and search visitors."""
    page = request.args.get('page', 1, type=int)
    filters = {
        'search': request.args.get('search', '').strip(),
        'status': request.args.get('status', '').strip(),
        'department_id': request.args.get('department_id', type=int),
        'date_from': request.args.get('date_from', '').strip(),
        'date_to': request.args.get('date_to', '').strip(),
    }
    filters = {k: v for k, v in filters.items() if v}

    if current_user.role == 'employee':
        emp = Employee.get_by_user_id(current_user.id)
        if emp:
            filters['host_employee_id'] = emp['id']

    result = Visitor.search(filters, page=page)
    departments = Department.get_all()

    return render_template(
        'visitors/list.html',
        visitors=result['items'],
        pagination=result,
        filters=filters,
        departments=departments,
    )


@visitors_bp.route('/register', methods=['GET', 'POST'])
@receptionist_required
def register():
    """Register a new visitor with photo and ID proof upload."""
    employees = Employee.get_all()

    if request.method == 'POST':
        try:
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            phone = request.form.get('phone', '').strip()
            purpose = request.form.get('purpose', '').strip()
            host_id = request.form.get('host_employee_id', type=int)

            if not all([first_name, last_name, phone, purpose, host_id]):
                flash('Please fill all required fields.', 'danger')
                return render_template('visitors/register.html', employees=employees)

            photo_path = None
            id_proof_path = None
            if 'photo' in request.files:
                photo_path = save_upload(request.files['photo'], 'photos')
            if 'id_proof' in request.files:
                id_proof_path = save_upload(request.files['id_proof'], 'id_proofs')

            visitor_code = generate_visitor_code()
            visitor_id = Visitor.create({
                'visitor_code': visitor_code,
                'first_name': first_name,
                'last_name': last_name,
                'email': request.form.get('email', '').strip(),
                'phone': phone,
                'company': request.form.get('company', '').strip(),
                'purpose': purpose,
                'host_employee_id': host_id,
                'photo_path': photo_path,
                'id_proof_path': id_proof_path,
                'id_proof_type': request.form.get('id_proof_type', '').strip(),
                'status': 'pending',
                'created_by': current_user.id,
                'notes': request.form.get('notes', '').strip(),
            })

            VisitorApproval.create(visitor_id, host_id)
            log_audit(current_user.id, 'visitor_registered', 'visitor', visitor_id,
                      visitor_code, get_client_ip(request))

            flash(f'Visitor registered successfully. Code: {visitor_code}', 'success')
            return redirect(url_for('visitors.detail', visitor_id=visitor_id))

        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')

    return render_template('visitors/register.html', employees=employees)


@visitors_bp.route('/<int:visitor_id>')
@login_required
def detail(visitor_id):
    """Visitor detail page."""
    visitor = Visitor.get_by_id(visitor_id)
    if not visitor:
        flash('Visitor not found.', 'danger')
        return redirect(url_for('visitors.list_visitors'))

    if current_user.role == 'employee':
        emp = Employee.get_by_user_id(current_user.id)
        if emp and visitor['host_employee_id'] != emp['id']:
            flash('Access denied.', 'danger')
            return redirect(url_for('visitors.list_visitors'))

    approval = VisitorApproval.get_by_visitor(visitor_id)
    return render_template('visitors/detail.html', visitor=visitor, approval=approval)


@visitors_bp.route('/<int:visitor_id>/approve', methods=['POST'])
@role_required('admin', 'employee')
def approve(visitor_id):
    """Employee approves visitor request."""
    emp = Employee.get_by_user_id(current_user.id)
    if not emp and current_user.role != 'admin':
        flash('Employee profile not found.', 'danger')
        return redirect(url_for('visitors.detail', visitor_id=visitor_id))

    approval = VisitorApproval.get_by_visitor(visitor_id)
    if not approval or approval['status'] != 'pending':
        flash('No pending approval found.', 'warning')
        return redirect(url_for('visitors.detail', visitor_id=visitor_id))

    if current_user.role == 'employee' and approval['employee_id'] != emp['id']:
        flash('You cannot approve this visitor.', 'danger')
        return redirect(url_for('visitors.detail', visitor_id=visitor_id))

    comments = request.form.get('comments', '').strip()
    VisitorApproval.approve(approval['id'], approval['employee_id'], comments)
    Visitor.update_status(visitor_id, 'approved')

    visitor = Visitor.get_by_id(visitor_id)
    qr_path = generate_visitor_qr({
        'id': visitor['id'],
        'visitor_code': visitor['visitor_code'],
        'first_name': visitor['first_name'],
        'last_name': visitor['last_name'],
        'host_name': visitor['host_name'],
        'status': 'approved',
        'badge_number': visitor.get('badge_number', ''),
    })
    Visitor.update_qr_path(visitor_id, qr_path)

    log_audit(current_user.id, 'visitor_approved', 'visitor', visitor_id,
              comments, get_client_ip(request))
    flash('Visitor approved. QR pass generated.', 'success')
    return redirect(url_for('visitors.detail', visitor_id=visitor_id))


@visitors_bp.route('/<int:visitor_id>/reject', methods=['POST'])
@role_required('admin', 'employee')
def reject(visitor_id):
    """Employee rejects visitor request."""
    emp = Employee.get_by_user_id(current_user.id)
    approval = VisitorApproval.get_by_visitor(visitor_id)
    if not approval or approval['status'] != 'pending':
        flash('No pending approval found.', 'warning')
        return redirect(url_for('visitors.detail', visitor_id=visitor_id))

    if current_user.role == 'employee' and emp and approval['employee_id'] != emp['id']:
        flash('You cannot reject this visitor.', 'danger')
        return redirect(url_for('visitors.detail', visitor_id=visitor_id))

    comments = request.form.get('comments', '').strip()
    VisitorApproval.reject(approval['id'], approval['employee_id'], comments)
    Visitor.update_status(visitor_id, 'rejected')
    log_audit(current_user.id, 'visitor_rejected', 'visitor', visitor_id,
              comments, get_client_ip(request))
    flash('Visitor request rejected.', 'info')
    return redirect(url_for('visitors.detail', visitor_id=visitor_id))


@visitors_bp.route('/<int:visitor_id>/check-in', methods=['POST'])
@receptionist_required
def check_in(visitor_id):
    """Check in an approved visitor."""
    visitor = Visitor.get_by_id(visitor_id)
    if not visitor:
        flash('Visitor not found.', 'danger')
        return redirect(url_for('visitors.list_visitors'))

    if visitor['status'] != 'approved':
        flash('Only approved visitors can check in.', 'warning')
        return redirect(url_for('visitors.detail', visitor_id=visitor_id))

    badge = request.form.get('badge_number') or generate_badge_number()
    Visitor.check_in(visitor_id, badge)
    log_audit(current_user.id, 'visitor_check_in', 'visitor', visitor_id,
              badge, get_client_ip(request))
    flash(f'Visitor checked in. Badge: {badge}', 'success')
    return redirect(url_for('visitors.detail', visitor_id=visitor_id))


@visitors_bp.route('/<int:visitor_id>/check-out', methods=['POST'])
@receptionist_required
def check_out(visitor_id):
    """Check out a visitor."""
    visitor = Visitor.get_by_id(visitor_id)
    if not visitor or visitor['status'] != 'checked_in':
        flash('Visitor is not checked in.', 'warning')
        return redirect(url_for('visitors.detail', visitor_id=visitor_id))

    Visitor.check_out(visitor_id)
    log_audit(current_user.id, 'visitor_check_out', 'visitor', visitor_id,
              None, get_client_ip(request))
    flash('Visitor checked out successfully.', 'success')
    return redirect(url_for('visitors.detail', visitor_id=visitor_id))


@visitors_bp.route('/<int:visitor_id>/pass')
@login_required
def visitor_pass(visitor_id):
    """Display printable visitor pass with QR code."""
    visitor = Visitor.get_by_id(visitor_id)
    if not visitor:
        flash('Visitor not found.', 'danger')
        return redirect(url_for('visitors.list_visitors'))
    return render_template('visitors/pass.html', visitor=visitor)


@visitors_bp.route('/tracking')
@login_required
def tracking():
    """Real-time visitor tracking - currently checked in."""
    active = Visitor.get_active_visitors()
    return render_template('visitors/tracking.html', visitors=active)


@visitors_bp.route('/approvals')
@role_required('admin', 'employee')
def approvals():
    """Pending approval queue for employees."""
    emp = Employee.get_by_user_id(current_user.id)
    pending = []
    if emp:
        pending = VisitorApproval.get_pending_for_employee(emp['id'])
    elif current_user.role == 'admin':
        pending = Visitor.search({'status': 'pending'}, page=1, per_page=50)['items']
    return render_template('visitors/approvals.html', pending=pending)
