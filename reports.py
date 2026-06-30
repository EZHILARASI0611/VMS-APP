"""
Reports module: daily, weekly, monthly reports with CSV/Excel export.
"""
from datetime import datetime, timedelta
from io import BytesIO
from flask import Blueprint, render_template, request, Response, send_file
from flask_login import login_required
from app.models.visitor import Visitor
from app.utils.decorators import role_required
from app.utils.export import export_visitors_csv, export_visitors_excel

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


def _parse_date_range(period):
    """Return date_from, date_to based on period type."""
    today = datetime.now().date()
    if period == 'daily':
        return today, today
    elif period == 'weekly':
        start = today - timedelta(days=today.weekday())
        return start, today
    elif period == 'monthly':
        start = today.replace(day=1)
        return start, today
    else:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        if date_from and date_to:
            return datetime.strptime(date_from, '%Y-%m-%d').date(), \
                   datetime.strptime(date_to, '%Y-%m-%d').date()
        start = today - timedelta(days=30)
        return start, today


@reports_bp.route('/')
@login_required
@role_required('admin', 'receptionist')
def index():
    """Reports dashboard."""
    period = request.args.get('period', 'daily')
    date_from, date_to = _parse_date_range(period)

    visitors = Visitor.get_report_data(
        date_from.strftime('%Y-%m-%d'),
        date_to.strftime('%Y-%m-%d')
    )

    summary = {
        'total': len(visitors),
        'pending': sum(1 for v in visitors if v['status'] == 'pending'),
        'approved': sum(1 for v in visitors if v['status'] == 'approved'),
        'checked_in': sum(1 for v in visitors if v['status'] == 'checked_in'),
        'checked_out': sum(1 for v in visitors if v['status'] == 'checked_out'),
        'rejected': sum(1 for v in visitors if v['status'] == 'rejected'),
    }

    return render_template(
        'reports/index.html',
        visitors=visitors,
        summary=summary,
        period=period,
        date_from=date_from,
        date_to=date_to,
    )


@reports_bp.route('/export')
@login_required
@role_required('admin', 'receptionist')
def export():
    """Export report as CSV or Excel."""
    fmt = request.args.get('format', 'csv')
    period = request.args.get('period', 'monthly')
    date_from, date_to = _parse_date_range(period)

    visitors = Visitor.get_report_data(
        date_from.strftime('%Y-%m-%d'),
        date_to.strftime('%Y-%m-%d')
    )

    filename_base = f"vms_report_{date_from}_{date_to}"

    if fmt == 'excel':
        data = export_visitors_excel(visitors)
        return send_file(
            BytesIO(data),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{filename_base}.xlsx',
        )

    csv_data = export_visitors_csv(visitors)
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename_base}.csv'},
    )
