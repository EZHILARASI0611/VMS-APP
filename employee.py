"""
Employee model operations.
"""
from app.utils.db import execute_query


class Employee:
    """Employee CRUD and lookup operations."""

    BASE_SELECT = """
        SELECT e.*, d.name AS department_name,
               u.username, u.email AS user_email
        FROM employees e
        JOIN departments d ON e.department_id = d.id
        LEFT JOIN users u ON e.user_id = u.id
    """

    @staticmethod
    def get_all(active_only=True):
        query = Employee.BASE_SELECT
        if active_only:
            query += ' WHERE e.is_active = 1'
        query += ' ORDER BY e.first_name, e.last_name'
        return execute_query(query, fetchall=True) or []

    @staticmethod
    def get_by_id(emp_id):
        return execute_query(
            Employee.BASE_SELECT + ' WHERE e.id = %s',
            (emp_id,), fetchone=True
        )

    @staticmethod
    def get_by_user_id(user_id):
        return execute_query(
            Employee.BASE_SELECT + ' WHERE e.user_id = %s AND e.is_active = 1',
            (user_id,), fetchone=True
        )

    @staticmethod
    def create(data):
        return execute_query(
            """INSERT INTO employees
               (user_id, department_id, employee_code, first_name, last_name,
                phone, email, designation)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                data.get('user_id'), data['department_id'], data['employee_code'],
                data['first_name'], data['last_name'], data.get('phone'),
                data.get('email'), data.get('designation'),
            ),
            commit=True,
        )

    @staticmethod
    def update(emp_id, data):
        execute_query(
            """UPDATE employees SET
               user_id=%s, department_id=%s, employee_code=%s,
               first_name=%s, last_name=%s, phone=%s, email=%s,
               designation=%s, is_active=%s
               WHERE id=%s""",
            (
                data.get('user_id'), data['department_id'], data['employee_code'],
                data['first_name'], data['last_name'], data.get('phone'),
                data.get('email'), data.get('designation'), data.get('is_active', 1),
                emp_id,
            ),
            commit=True,
        )

    @staticmethod
    def delete(emp_id):
        execute_query(
            'UPDATE employees SET is_active=0 WHERE id=%s',
            (emp_id,), commit=True
        )

    @staticmethod
    def count():
        row = execute_query(
            'SELECT COUNT(*) AS cnt FROM employees WHERE is_active=1',
            fetchone=True
        )
        return row['cnt'] if row else 0

    @staticmethod
    def full_name(employee):
        if not employee:
            return ''
        return f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
