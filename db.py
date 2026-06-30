"""
Database connection utilities using PyMySQL.
Provides a connection pool pattern via context manager.
"""
import pymysql
from flask import current_app, g


def get_db_config():
    """Return database connection parameters from Flask config."""
    return {
        'host': current_app.config['DB_HOST'],
        'port': current_app.config['DB_PORT'],
        'user': current_app.config['DB_USER'],
        'password': current_app.config['DB_PASSWORD'],
        'database': current_app.config['DB_NAME'],
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'autocommit': False,
    }


def get_db():
    """Get or create a database connection for the current request."""
    if 'db' not in g:
        g.db = pymysql.connect(**get_db_config())
    return g.db


def close_db(e=None):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db_app(app):
    """Register teardown handler with Flask app."""
    app.teardown_appcontext(close_db)


def execute_query(query, params=None, fetchone=False, fetchall=False, commit=False):
    """
    Execute a SQL query and optionally return results.
    Uses the request-scoped connection.
    """
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(query, params or ())
        if commit:
            db.commit()
            return cursor.lastrowid
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
        return cursor.rowcount
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


def execute_many(query, params_list, commit=True):
    """Execute batch insert/update."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.executemany(query, params_list)
        if commit:
            db.commit()
        return cursor.rowcount
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
