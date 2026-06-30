# Visitor Management System (VMS)

A production-ready corporate Visitor Management System built with **Flask**, **MySQL**, **Bootstrap 5**, and **JavaScript**.

## Features

- **Role-Based Access Control** — Admin, Employee, Receptionist
- **Visitor Registration** with photo and ID proof upload
- **Employee Approval Workflow**
- **Check-In / Check-Out** with badge assignment
- **Live Visitor Tracking**
- **QR Code Visitor Pass** generation and printing
- **Analytics Dashboard** with Chart.js
- **Daily, Weekly, Monthly Reports** with CSV/Excel export
- **User, Employee, Department Management** (Admin)
- **Search & Filter** visitors
- **REST API** endpoints

## Project Structure

```
VSM APP/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration
│   ├── models/              # Data models (User, Visitor, Employee, etc.)
│   ├── routes/              # Blueprints (auth, visitors, admin, reports, api)
│   ├── utils/               # Helpers (DB, QR, export, decorators)
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS, JS, uploads, QR codes
├── database/
│   ├── schema.sql           # MySQL schema + seed departments/employees
│   └── seed_users.py        # Create default login accounts
├── docs/
│   ├── API_DOCUMENTATION.md
│   └── DEPLOYMENT_GUIDE.md
├── requirements.txt
├── run.py                   # Application entry point
└── .env.example
```

## Quick Start (VS Code)

### Prerequisites

- Python 3.10+
- MySQL 8.0+

### 1. Install Dependencies

```bash
cd "VSM APP"
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
```

Edit `.env` with your MySQL credentials:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=vms_db
SECRET_KEY=your-random-secret-key
```

### 3. Create Database

```bash
mysql -u root -p < database/schema.sql
python database/seed_users.py
```

### 4. Run Application

```bash
python run.py
```

Open **http://localhost:5000**

### Default Login Accounts

| Role         | Username      | Password       |
|--------------|---------------|----------------|
| Admin        | admin         | Admin@123      |
| Receptionist | receptionist  | Reception@123  |
| Employee     | employee1     | Employee@123   |

## Workflow

1. **Receptionist** registers a visitor and selects a host employee
2. **Employee** (host) approves or rejects the visit request
3. On approval, a **QR visitor pass** is generated
4. **Receptionist** checks in the visitor at arrival (badge assigned)
5. **Receptionist** checks out the visitor on departure
6. **Admin/Receptionist** generates reports and exports data

## Documentation

- [API Documentation](docs/API_DOCUMENTATION.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)

## License

MIT License — free for corporate and educational use.
