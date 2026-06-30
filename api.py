"""
REST API endpoints for VMS.
All endpoints return JSON responses.
"""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models.visitor import Visitor, VisitorApproval
from app.models.employee import Employee
from app.models.department import Department
from app.utils.decorators import role_required
from app.utils.helpers import generate_visitor_code, log_audit, get_client_ip
from app.utils.qr_generator import generate_visitor_qr

api_bp = Blueprint('api', __name__)


def api_response(success=True, message='', data=None, status=200):
    """Standard API response wrapper."""
    return jsonify({
        'success': success,
        'message': message,
        'data': data,
    }), status


# ---- Auth API ----

@api_bp.route('/auth/me', methods=['GET'])
@login_required
def api_me():
    """Get current authenticated user."""
    return api_response(data=current_user.to_dict())


# ---- Dashboard API ----

@api_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def api_dashboard_stats():
    """Dashboard analytics data."""
    return api_response(data={
        'visitors_today': Visitor.count_today(),
        'checked_in_now': len(Visitor.get_active_visitors()),
        'employees': Employee.count(),
        'departments': Department.count(),
        'status_breakdown': Visitor.count_by_status(),
        'daily_stats': Visitor.daily_stats(7),
        'monthly_stats': Visitor.monthly_stats(6),
    })


# ---- Visitors API ----

@api_bp.route('/visitors', methods=['GET'])
@login_required
def api_list_visitors():
    """List visitors with search/filter."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)
    filters = {
        'search': request.args.get('search', ''),
        'status': request.args.get('status', ''),
        'department_id': request.args.get('department_id', type=int),
        'date_from': request.args.get('date_from', ''),
        'date_to': request.args.get('date_to', ''),
    }
    filters = {k: v for k, v in filters.items() if v}

    if current_user.role == 'employee':
        emp = Employee.get_by_user_id(current_user.id)
        if emp:
            filters['host_employee_id'] = emp['id']

    result = Visitor.search(filters, page=page, per_page=per_page)
    return api_response(data=result)


@api_bp.route('/visitors/<int:visitor_id>', methods=['GET'])
@login_required
def api_get_visitor(visitor_id):
    """Get single visitor details."""
    visitor = Visitor.get_by_id(visitor_id)
    if not visitor:
        return api_response(False, 'Visitor not found', status=404)
    approval = VisitorApproval.get_by_visitor(visitor_id)
    return api_response(data={'visitor': visitor, 'approval': approval})


@api_bp.route('/visitors', methods=['POST'])
@login_required
@role_required('admin', 'receptionist')
def api_create_visitor():
    """Register visitor via API."""
    data = request.get_json() or {}
    required = ['first_name', 'last_name', 'phone', 'purpose', 'host_employee_id']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return api_response(False, f'Missing fields: {", ".join(missing)}', status=400)

    visitor_code = generate_visitor_code()
    visitor_id = Visitor.create({
        'visitor_code': visitor_code,
        'first_name': data['first_name'],
        'last_name': data['last_name'],
        'email': data.get('email'),
        'phone': data['phone'],
        'company': data.get('company'),
        'purpose': data['purpose'],
        'host_employee_id': data['host_employee_id'],
        'id_proof_type': data.get('id_proof_type'),
        'status': 'pending',
        'created_by': current_user.id,
        'notes': data.get('notes'),
    })
    VisitorApproval.create(visitor_id, data['host_employee_id'])
    visitor = Visitor.get_by_id(visitor_id)
    return api_response(True, 'Visitor registered', data=visitor, status=201)


@api_bp.route('/visitors/<int:visitor_id>/check-in', methods=['POST'])
@login_required
@role_required('admin', 'receptionist')
def api_check_in(visitor_id):
    """Check in visitor via API."""
    from app.utils.helpers import generate_badge_number
    visitor = Visitor.get_by_id(visitor_id)
    if not visitor:
        return api_response(False, 'Visitor not found', status=404)
    if visitor['status'] != 'approved':
        return api_response(False, 'Visitor must be approved first', status=400)

    data = request.get_json() or {}
    badge = data.get('badge_number') or generate_badge_number()
    Visitor.check_in(visitor_id, badge)
    return api_response('Checked in', data=Visitor.get_by_id(visitor_id))


@api_bp.route('/visitors/<int:visitor_id>/check-out', methods=['POST'])
@login_required
@role_required('admin', 'receptionist')
def api_check_out(visitor_id):
    """Check out visitor via API."""
    visitor = Visitor.get_by_id(visitor_id)
    if not visitor or visitor['status'] != 'checked_in':
        return api_response(False, 'Visitor not checked in', status=400)
    Visitor.check_out(visitor_id)
    return api_response('Checked out', data=Visitor.get_by_id(visitor_id))


@api_bp.route('/visitors/<int:visitor_id>/approve', methods=['POST'])
@login_required
@role_required('admin', 'employee')
def api_approve(visitor_id):
    """Approve visitor via API."""
    approval = VisitorApproval.get_by_visitor(visitor_id)
    if not approval or approval['status'] != 'pending':
        return api_response(False, 'No pending approval', status=400)

    data = request.get_json() or {}
    VisitorApproval.approve(approval['id'], approval['employee_id'],
                            data.get('comments', ''))
    Visitor.update_status(visitor_id, 'approved')

    visitor = Visitor.get_by_id(visitor_id)
    qr_path = generate_visitor_qr({
        'id': visitor['id'],
        'visitor_code': visitor['visitor_code'],
        'first_name': visitor['first_name'],
        'last_name': visitor['last_name'],
        'host_name': visitor['host_name'],
        'status': 'approved',
    })
    Visitor.update_qr_path(visitor_id, qr_path)
    return api_response('Approved', data=Visitor.get_by_id(visitor_id))


@api_bp.route('/visitors/<int:visitor_id>/reject', methods=['POST'])
@login_required
@role_required('admin', 'employee')
def api_reject(visitor_id):
    """Reject visitor via API."""
    approval = VisitorApproval.get_by_visitor(visitor_id)
    if not approval or approval['status'] != 'pending':
        return api_response(False, 'No pending approval', status=400)
    data = request.get_json() or {}
    VisitorApproval.reject(approval['id'], approval['employee_id'],
                           data.get('comments', ''))
    Visitor.update_status(visitor_id, 'rejected')
    return api_response('Rejected', data=Visitor.get_by_id(visitor_id))


@api_bp.route('/visitors/active', methods=['GET'])
@login_required
def api_active_visitors():
    """Currently checked-in visitors."""
    return api_response(data=Visitor.get_active_visitors())


@api_bp.route('/visitors/code/<visitor_code>', methods=['GET'])
@login_required
def api_visitor_by_code(visitor_code):
    """Lookup visitor by code (for QR scan)."""
    visitor = Visitor.get_by_code(visitor_code)
    if not visitor:
        return api_response(False, 'Visitor not found', status=404)
    return api_response(data=visitor)


# ---- Employees & Departments API ----

@api_bp.route('/employees', methods=['GET'])
@login_required
def api_employees():
    """List all active employees."""
    return api_response(data=Employee.get_all())


@api_bp.route('/departments', methods=['GET'])
@login_required
def api_departments():
    """List all active departments."""
    return api_response(data=Department.get_all())


# ---- Reports API ----

@api_bp.route('/reports', methods=['GET'])
@login_required
@role_required('admin', 'receptionist')
def api_reports():
    """Get report data for date range."""
    period = request.args.get('period', 'monthly')
    today = datetime.now().date()
    if period == 'daily':
        date_from = date_to = today
    elif period == 'weekly':
        date_from = today - timedelta(days=today.weekday())
        date_to = today
    else:
        date_from = today.replace(day=1)
        date_to = today

    df = request.args.get('date_from')
    dt = request.args.get('date_to')
    if df and dt:
        date_from = datetime.strptime(df, '%Y-%m-%d').date()
        date_to = datetime.strptime(dt, '%Y-%m-%d').date()

    visitors = Visitor.get_report_data(
        date_from.strftime('%Y-%m-%d'),
        date_to.strftime('%Y-%m-%d')
    )
    return api_response(data={
        'date_from': str(date_from),
        'date_to': str(date_to),
        'total': len(visitors),
        'visitors': visitors,
    })
