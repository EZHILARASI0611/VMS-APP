"""
User model and authentication operations.
"""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.db import execute_query


class User(UserMixin):
    """User model representing admin, employee, or receptionist."""

    def __init__(self, id, username, email, password_hash, role, is_active=True,
                 last_login=None, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.is_active_user = is_active
        self.last_login = last_login
        self.created_at = created_at

    @property
    def is_active(self):
        return bool(self.is_active_user)

    def get_id(self):
        return str(self.id)

    @staticmethod
    def get_by_id(user_id):
        row = execute_query(
            'SELECT * FROM users WHERE id = %s AND is_active = 1',
            (user_id,), fetchone=True
        )
        return User._from_row(row) if row else None

    @staticmethod
    def get_by_username(username):
        row = execute_query(
            'SELECT * FROM users WHERE username = %s AND is_active = 1',
            (username,), fetchone=True
        )
        return User._from_row(row) if row else None

    @staticmethod
    def get_by_email(email):
        row = execute_query(
            'SELECT * FROM users WHERE email = %s',
            (email,), fetchone=True
        )
        return User._from_row(row) if row else None

    @staticmethod
    def get_all(role=None):
        if role:
            rows = execute_query(
                'SELECT * FROM users ORDER BY created_at DESC',
                fetchall=True
            )
            return [User._from_row(r) for r in rows if r['role'] == role]
        rows = execute_query('SELECT * FROM users ORDER BY created_at DESC', fetchall=True)
        return [User._from_row(r) for r in rows]

    @staticmethod
    def create(username, email, password, role):
        password_hash = generate_password_hash(password)
        user_id = execute_query(
            """INSERT INTO users (username, email, password_hash, role)
               VALUES (%s, %s, %s, %s)""",
            (username, email, password_hash, role),
            commit=True,
        )
        return user_id

    @staticmethod
    def update(user_id, username, email, role, is_active):
        execute_query(
            """UPDATE users SET username=%s, email=%s, role=%s, is_active=%s
               WHERE id=%s""",
            (username, email, role, is_active, user_id),
            commit=True,
        )

    @staticmethod
    def update_password(user_id, password):
        password_hash = generate_password_hash(password)
        execute_query(
            'UPDATE users SET password_hash=%s WHERE id=%s',
            (password_hash, user_id),
            commit=True,
        )

    @staticmethod
    def delete(user_id):
        execute_query('UPDATE users SET is_active=0 WHERE id=%s', (user_id,), commit=True)

    @staticmethod
    def verify_password(user, password):
        return check_password_hash(user.password_hash, password)

    @staticmethod
    def update_last_login(user_id):
        execute_query(
            'UPDATE users SET last_login = NOW() WHERE id = %s',
            (user_id,), commit=True
        )

    @staticmethod
    def _from_row(row):
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            role=row['role'],
            is_active=row['is_active'],
            last_login=row.get('last_login'),
            created_at=row.get('created_at'),
        )

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active_user,
            'last_login': str(self.last_login) if self.last_login else None,
        }
