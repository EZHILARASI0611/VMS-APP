"""
Database seed script - creates default users with hashed passwords.
Run after schema.sql: python database/seed_users.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash
import pymysql
from dotenv import load_dotenv

load_dotenv()

USERS = [
    ('admin', 'admin@vms.local', 'Admin@123', 'admin'),
    ('receptionist', 'reception@vms.local', 'Reception@123', 'receptionist'),
    ('employee1', 'employee1@vms.local', 'Employee@123', 'employee'),
]


def main():
    conn = pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'vms_db'),
        charset='utf8mb4',
    )
    cursor = conn.cursor()
    try:
        for username, email, password, role in USERS:
            pw_hash = generate_password_hash(password)
            cursor.execute(
                """INSERT INTO users (username, email, password_hash, role)
                   VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash),
                   email = VALUES(email), role = VALUES(role)""",
                (username, email, pw_hash, role),
            )
            print(f'  Seeded user: {username} / {password} ({role})')

        cursor.execute(
            "UPDATE employees SET user_id = (SELECT id FROM users WHERE username='employee1') "
            "WHERE employee_code='EMP003'"
        )
        conn.commit()
        print('\nSeed completed successfully.')
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
