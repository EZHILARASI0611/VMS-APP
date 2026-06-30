# VMS Deployment Guide

This guide covers deploying the Visitor Management System to a production environment.

---

## 1. System Requirements

| Component | Minimum              |
|-----------|----------------------|
| OS        | Ubuntu 22.04 / Windows Server |
| Python    | 3.10+                |
| MySQL     | 8.0+                 |
| RAM       | 2 GB                 |
| Disk      | 10 GB (+ uploads)    |

---

## 2. Production Environment Setup

### 2.1 Clone and Install

```bash
git clone <your-repo-url> /opt/vms
cd /opt/vms
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### 2.2 MySQL Database

```bash
mysql -u root -p < database/schema.sql
python database/seed_users.py
```

Create a dedicated MySQL user:

```sql
CREATE USER 'vms_user'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON vms_db.* TO 'vms_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2.3 Environment Variables

Create `/opt/vms/.env`:

```env
FLASK_ENV=production
SECRET_KEY=<generate-with-python -c "import secrets; print(secrets.token_hex(32))">
DB_HOST=localhost
DB_PORT=3306
DB_USER=vms_user
DB_PASSWORD=strong_password_here
DB_NAME=vms_db
```

**Important:** Change all default passwords after first login.

---

## 3. Run with Gunicorn

```bash
cd /opt/vms
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:8000 "run:app"
```

Recommended workers: `(2 × CPU cores) + 1`

---

## 4. Nginx Reverse Proxy (Linux)

```nginx
server {
    listen 80;
    server_name vms.yourcompany.com;

    client_max_body_size 16M;

    location /static {
        alias /opt/vms/app/static;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable HTTPS with Let's Encrypt:

```bash
sudo certbot --nginx -d vms.yourcompany.com
```

---

## 5. Systemd Service

Create `/etc/systemd/system/vms.service`:

```ini
[Unit]
Description=Visitor Management System
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/vms
Environment="PATH=/opt/vms/venv/bin"
EnvironmentFile=/opt/vms/.env
ExecStart=/opt/vms/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 "run:app"
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable vms
sudo systemctl start vms
sudo systemctl status vms
```

---

## 6. Windows IIS / Production (Alternative)

1. Install Python and MySQL on Windows Server
2. Use `waitress` instead of gunicorn:

```bash
pip install waitress
waitress-serve --port=8000 run:app
```

3. Configure IIS as reverse proxy with URL Rewrite + ARR

---

## 7. Security Checklist

- [ ] Change `SECRET_KEY` to a random 32+ byte value
- [ ] Change all default user passwords
- [ ] Use HTTPS in production
- [ ] Restrict MySQL to localhost
- [ ] Set proper file permissions on `app/static/uploads/`
- [ ] Enable MySQL backups (daily)
- [ ] Review audit_logs table periodically
- [ ] Disable Flask debug mode (`FLASK_ENV=production`)

---

## 8. Backup Strategy

### Database Backup (daily cron)

```bash
0 2 * * * mysqldump -u vms_user -p'password' vms_db > /backups/vms_$(date +\%Y\%m\%d).sql
```

### Upload Files

Backup `app/static/uploads/` and `app/static/qr_codes/` regularly.

---

## 9. VS Code Development

1. Open the `VSM APP` folder in VS Code
2. Install Python extension
3. Select the virtual environment interpreter
4. Create `.env` from `.env.example`
5. Run via terminal: `python run.py`
6. Or use launch configuration:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "VMS Flask",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/run.py",
      "console": "integratedTerminal"
    }
  ]
}
```

---

## 10. Troubleshooting

| Issue | Solution |
|-------|----------|
| `Access denied for user` | Check `.env` DB credentials |
| `ModuleNotFoundError` | Activate venv, run `pip install -r requirements.txt` |
| Upload fails | Check folder permissions on `app/static/uploads/` |
| QR not generated | Ensure `Pillow` and `qrcode` installed |
| Session expires | Adjust `PERMANENT_SESSION_LIFETIME` in `config.py` |

---

## 11. Monitoring

- Check application logs: `journalctl -u vms -f`
- Monitor MySQL: `SHOW PROCESSLIST;`
- Review audit trail: `SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 50;`
