"""
Main routes: dashboard and home.
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.visitor import Visitor
from app.models.employee import Employee
from app.models.department import Department

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Redirect root to dashboard or login."""
    from flask import redirect, url_for
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Role-aware analytics dashboard."""
    stats = {
        'total_visitors_today': Visitor.count_today(),
        'checked_in_now': len(Visitor.get_active_visitors()),
        'total_employees': Employee.count(),
        'total_departments': Department.count(),
        'status_breakdown': Visitor.count_by_status(),
        'daily_stats': Visitor.daily_stats(7),
        'monthly_stats': Visitor.monthly_stats(6),
    }

    recent_visitors = Visitor.search(page=1, per_page=5)['items']
    active_visitors = Visitor.get_active_visitors()[:10]

    pending_approvals = []
    if current_user.role == 'employee':
        from app.models.employee import Employee as Emp
        from app.models.visitor import VisitorApproval
        emp = Emp.get_by_user_id(current_user.id)
        if emp:
            pending_approvals = VisitorApproval.get_pending_for_employee(emp['id'])

    return render_template(
        'dashboard.html',
        stats=stats,
        recent_visitors=recent_visitors,
        active_visitors=active_visitors,
        pending_approvals=pending_approvals,
    )
