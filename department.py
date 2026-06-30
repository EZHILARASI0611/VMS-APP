"""
Department model operations.
"""
from app.utils.db import execute_query


class Department:
    """Department CRUD operations."""

    @staticmethod
    def get_all(active_only=True):
        query = 'SELECT * FROM departments'
        if active_only:
            query += ' WHERE is_active = 1'
        query += ' ORDER BY name'
        return execute_query(query, fetchall=True) or []

    @staticmethod
    def get_by_id(dept_id):
        return execute_query(
            'SELECT * FROM departments WHERE id = %s',
            (dept_id,), fetchone=True
        )

    @staticmethod
    def create(name, description=''):
        return execute_query(
            'INSERT INTO departments (name, description) VALUES (%s, %s)',
            (name, description),
            commit=True,
        )

    @staticmethod
    def update(dept_id, name, description, is_active):
        execute_query(
            """UPDATE departments SET name=%s, description=%s, is_active=%s
               WHERE id=%s""",
            (name, description, is_active, dept_id),
            commit=True,
        )

    @staticmethod
    def delete(dept_id):
        execute_query(
            'UPDATE departments SET is_active=0 WHERE id=%s',
            (dept_id,), commit=True
        )

    @staticmethod
    def count():
        row = execute_query(
            'SELECT COUNT(*) AS cnt FROM departments WHERE is_active=1',
            fetchone=True
        )
        return row['cnt'] if row else 0
