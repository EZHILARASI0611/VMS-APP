"""
QR Code generation for visitor passes.
"""
import os
import json
import qrcode
from flask import current_app


def generate_visitor_qr(visitor_data):
    """
    Generate QR code image for a visitor pass.
    visitor_data: dict with visitor_id, visitor_code, name, host, etc.
    Returns relative path to QR image in static folder.
    """
    qr_folder = current_app.config['QR_FOLDER']
    os.makedirs(qr_folder, exist_ok=True)

    payload = {
        'visitor_id': visitor_data.get('id'),
        'visitor_code': visitor_data.get('visitor_code'),
        'name': f"{visitor_data.get('first_name', '')} {visitor_data.get('last_name', '')}".strip(),
        'host': visitor_data.get('host_name', ''),
        'status': visitor_data.get('status'),
        'badge': visitor_data.get('badge_number', ''),
    }

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(payload))
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')
    filename = f"qr_{visitor_data.get('visitor_code', 'unknown')}.png"
    filepath = os.path.join(qr_folder, filename)
    img.save(filepath)

    return os.path.join('qr_codes', filename).replace('\\', '/')
