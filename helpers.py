"""
Helper utilities for VMS.
"""
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename):
    """Check if file extension is allowed."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']


def save_upload(file, subfolder=''):
    """
    Save uploaded file and return relative path from static folder.
    Returns None if no file provided.
    """
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError('File type not allowed. Use PNG, JPG, JPEG, GIF, WEBP, or PDF.')

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    upload_dir = current_app.config['UPLOAD_FOLDER']
    if subfolder:
        upload_dir = os.path.join(upload_dir, subfolder)
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, unique_name)
    file.save(filepath)
    rel_path = os.path.join('uploads', subfolder, unique_name).replace('\\', '/')
    if subfolder == '':
        rel_path = os.path.join('uploads', unique_name).replace('\\', '/')
    return rel_path


def generate_visitor_code():
    """Generate unique visitor code like VIS-20250613-XXXX."""
    date_part = datetime.now().strftime('%Y%m%d')
    short_uuid = uuid.uuid4().hex[:6].upper()
    return f"VIS-{date_part}-{short_uuid}"


def generate_badge_number():
    """Generate visitor badge number."""
    return f"BDG-{datetime.now().strftime('%H%M')}-{uuid.uuid4().hex[:4].upper()}"


def format_datetime(dt):
    """Format datetime for display."""
    if not dt:
        return '-'
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt
    return dt.strftime('%d %b %Y, %I:%M %p')


def log_audit(user_id, action, entity_type=None, entity_id=None, details=None, ip_address=None):
    """Write audit log entry."""
    from app.utils.db import execute_query
    execute_query(
        """INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, ip_address)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (user_id, action, entity_type, entity_id, details, ip_address),
        commit=True,
    )


def get_client_ip(request):
    """Extract client IP from request."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or 'unknown'
