"""
Visitor model and related operations.
"""
from app.utils.db import execute_query


class Visitor:
    """Visitor registration, check-in/out, and tracking."""

    BASE_SELECT = """
        SELECT v.*,
               CONCAT(e.first_name, ' ', e.last_name) AS host_name,
               e.employee_code AS host_code,
               d.name AS department_name,
               CONCAT(u.username) AS created_by_name
        FROM visitors v
        JOIN employees e ON v.host_employee_id = e.id
        JOIN departments d ON e.department_id = d.id
        JOIN users u ON v.created_by = u.id
    """

    @staticmethod
    def get_by_id(visitor_id):
        return execute_query(
            Visitor.BASE_SELECT + ' WHERE v.id = %s',
            (visitor_id,), fetchone=True
        )

    @staticmethod
    def get_by_code(visitor_code):
        return execute_query(
            Visitor.BASE_SELECT + ' WHERE v.visitor_code = %s',
            (visitor_code,), fetchone=True
        )

    @staticmethod
    def search(filters=None, page=1, per_page=15):
        """Search and filter visitors with pagination."""
        filters = filters or {}
        conditions = []
        params = []

        if filters.get('search'):
            conditions.append(
                """(v.first_name LIKE %s OR v.last_name LIKE %s OR v.visitor_code LIKE %s
                    OR v.phone LIKE %s OR v.company LIKE %s OR v.email LIKE %s)"""
            )
            term = f"%{filters['search']}%"
            params.extend([term] * 6)

        if filters.get('status'):
            conditions.append('v.status = %s')
            params.append(filters['status'])

        if filters.get('host_employee_id'):
            conditions.append('v.host_employee_id = %s')
            params.append(filters['host_employee_id'])

        if filters.get('department_id'):
            conditions.append('e.department_id = %s')
            params.append(filters['department_id'])

        if filters.get('date_from'):
            conditions.append('DATE(v.created_at) >= %s')
            params.append(filters['date_from'])

        if filters.get('date_to'):
            conditions.append('DATE(v.created_at) <= %s')
            params.append(filters['date_to'])

        where_clause = ' WHERE ' + ' AND '.join(conditions) if conditions else ''

        count_row = execute_query(
            f"""SELECT COUNT(*) AS cnt FROM visitors v
                JOIN employees e ON v.host_employee_id = e.id
                {where_clause}""",
            tuple(params), fetchone=True
        )
        total = count_row['cnt'] if count_row else 0

        offset = (page - 1) * per_page
        rows = execute_query(
            Visitor.BASE_SELECT + where_clause +
            ' ORDER BY v.created_at DESC LIMIT %s OFFSET %s',
            tuple(params + [per_page, offset]),
            fetchall=True
        )

        return {
            'items': rows or [],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': max(1, (total + per_page - 1) // per_page),
        }

    @staticmethod
    def create(data):
        return execute_query(
            """INSERT INTO visitors
               (visitor_code, first_name, last_name, email, phone, company, purpose,
                host_employee_id, photo_path, id_proof_path, id_proof_type,
                status, created_by, notes)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                data['visitor_code'], data['first_name'], data['last_name'],
                data.get('email'), data['phone'], data.get('company'),
                data['purpose'], data['host_employee_id'],
                data.get('photo_path'), data.get('id_proof_path'),
                data.get('id_proof_type'), data.get('status', 'pending'),
                data['created_by'], data.get('notes'),
            ),
            commit=True,
        )

    @staticmethod
    def update_status(visitor_id, status, badge_number=None):
        params = [status, visitor_id]
        query = 'UPDATE visitors SET status = %s'
        if badge_number:
            query += ', badge_number = %s'
            params = [status, badge_number, visitor_id]
        query += ' WHERE id = %s'
        execute_query(query, tuple(params), commit=True)

    @staticmethod
    def update_qr_path(visitor_id, qr_path):
        execute_query(
            'UPDATE visitors SET qr_code_path = %s WHERE id = %s',
            (qr_path, visitor_id), commit=True
        )

    @staticmethod
    def check_in(visitor_id, badge_number=None):
        execute_query(
            """UPDATE visitors SET status='checked_in', check_in_time=NOW(),
               badge_number=COALESCE(%s, badge_number) WHERE id=%s AND status='approved'""",
            (badge_number, visitor_id), commit=True
        )

    @staticmethod
    def check_out(visitor_id):
        execute_query(
            """UPDATE visitors SET status='checked_out', check_out_time=NOW()
               WHERE id=%s AND status='checked_in'""",
            (visitor_id,), commit=True
        )

    @staticmethod
    def get_for_employee(employee_id, status=None):
        query = Visitor.BASE_SELECT + ' WHERE v.host_employee_id = %s'
        params = [employee_id]
        if status:
            query += ' AND v.status = %s'
            params.append(status)
        query += ' ORDER BY v.created_at DESC'
        return execute_query(query, tuple(params), fetchall=True) or []

    @staticmethod
    def get_active_visitors():
        """Currently checked-in visitors."""
        return execute_query(
            Visitor.BASE_SELECT + " WHERE v.status = 'checked_in' ORDER BY v.check_in_time DESC",
            fetchall=True
        ) or []

    @staticmethod
    def get_report_data(date_from, date_to):
        return execute_query(
            Visitor.BASE_SELECT +
            ' WHERE DATE(v.created_at) BETWEEN %s AND %s ORDER BY v.created_at DESC',
            (date_from, date_to), fetchall=True
        ) or []

    @staticmethod
    def count_by_status():
        return execute_query(
            """SELECT status, COUNT(*) AS count FROM visitors
               GROUP BY status""",
            fetchall=True
        ) or []

    @staticmethod
    def count_today():
        row = execute_query(
            "SELECT COUNT(*) AS cnt FROM visitors WHERE DATE(created_at) = CURDATE()",
            fetchone=True
        )
        return row['cnt'] if row else 0

    @staticmethod
    def count_checked_in_today():
        row = execute_query(
            """SELECT COUNT(*) AS cnt FROM visitors
               WHERE status='checked_in' OR (DATE(check_in_time)=CURDATE())""",
            fetchone=True
        )
        return row['cnt'] if row else 0

    @staticmethod
    def daily_stats(days=7):
        return execute_query(
            """SELECT DATE(created_at) AS date, COUNT(*) AS total,
                      SUM(CASE WHEN status='checked_in' THEN 1 ELSE 0 END) AS checked_in,
                      SUM(CASE WHEN status='checked_out' THEN 1 ELSE 0 END) AS checked_out
               FROM visitors
               WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
               GROUP BY DATE(created_at)
               ORDER BY date""",
            (days,), fetchall=True
        ) or []

    @staticmethod
    def monthly_stats(months=6):
        return execute_query(
            """SELECT DATE_FORMAT(created_at, '%%Y-%%m') AS month,
                      COUNT(*) AS total
               FROM visitors
               WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
               GROUP BY DATE_FORMAT(created_at, '%%Y-%%m')
               ORDER BY month""",
            (months,), fetchall=True
        ) or []


class VisitorApproval:
    """Visitor approval workflow."""

    @staticmethod
    def create(visitor_id, employee_id):
        return execute_query(
            """INSERT INTO visitor_approvals (visitor_id, employee_id, status)
               VALUES (%s, %s, 'pending')""",
            (visitor_id, employee_id), commit=True
        )

    @staticmethod
    def get_by_visitor(visitor_id):
        return execute_query(
            """SELECT va.*, CONCAT(e.first_name, ' ', e.last_name) AS employee_name
               FROM visitor_approvals va
               JOIN employees e ON va.employee_id = e.id
               WHERE va.visitor_id = %s ORDER BY va.created_at DESC LIMIT 1""",
            (visitor_id,), fetchone=True
        )

    @staticmethod
    def approve(approval_id, employee_id, comments=''):
        execute_query(
            """UPDATE visitor_approvals SET status='approved', comments=%s, approved_at=NOW()
               WHERE id=%s AND employee_id=%s""",
            (comments, approval_id, employee_id), commit=True
        )

    @staticmethod
    def reject(approval_id, employee_id, comments=''):
        execute_query(
            """UPDATE visitor_approvals SET status='rejected', comments=%s, approved_at=NOW()
               WHERE id=%s AND employee_id=%s""",
            (comments, approval_id, employee_id), commit=True
        )

    @staticmethod
    def get_pending_for_employee(employee_id):
        return execute_query(
            """SELECT va.*, v.visitor_code, v.first_name, v.last_name, v.company,
                      v.purpose, v.phone, v.created_at AS visitor_created
               FROM visitor_approvals va
               JOIN visitors v ON va.visitor_id = v.id
               WHERE va.employee_id = %s AND va.status = 'pending'
               ORDER BY va.created_at DESC""",
            (employee_id,), fetchall=True
        ) or []
