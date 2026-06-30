-- ============================================================
-- Visitor Management System (VMS) - Database Schema
-- MySQL 8.0+
-- ============================================================

CREATE DATABASE IF NOT EXISTS vms_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE vms_db;

-- ------------------------------------------------------------
-- Departments
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active   TINYINT(1) NOT NULL DEFAULT 1,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Users (Admin, Employee, Receptionist)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50) NOT NULL UNIQUE,
    email         VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('admin', 'employee', 'receptionist') NOT NULL,
    is_active     TINYINT(1) NOT NULL DEFAULT 1,
    last_login    DATETIME NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_role (role),
    INDEX idx_users_active (is_active)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Employees (linked to users)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employees (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NULL,
    department_id  INT NOT NULL,
    employee_code  VARCHAR(20) NOT NULL UNIQUE,
    first_name     VARCHAR(80) NOT NULL,
    last_name      VARCHAR(80) NOT NULL,
    phone          VARCHAR(20),
    email          VARCHAR(120),
    designation    VARCHAR(100),
    is_active      TINYINT(1) NOT NULL DEFAULT 1,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_employees_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_employees_department FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE RESTRICT,
    INDEX idx_employees_department (department_id),
    INDEX idx_employees_active (is_active)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Visitors
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS visitors (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    visitor_code      VARCHAR(20) NOT NULL UNIQUE,
    first_name        VARCHAR(80) NOT NULL,
    last_name         VARCHAR(80) NOT NULL,
    email             VARCHAR(120),
    phone             VARCHAR(20) NOT NULL,
    company           VARCHAR(150),
    purpose           TEXT NOT NULL,
    host_employee_id  INT NOT NULL,
    photo_path        VARCHAR(255),
    id_proof_path     VARCHAR(255),
    id_proof_type     VARCHAR(50),
    status            ENUM('pending', 'approved', 'rejected', 'checked_in', 'checked_out', 'cancelled') NOT NULL DEFAULT 'pending',
    check_in_time     DATETIME NULL,
    check_out_time    DATETIME NULL,
    qr_code_path      VARCHAR(255),
    badge_number      VARCHAR(30),
    notes             TEXT,
    created_by        INT NOT NULL,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_visitors_host FOREIGN KEY (host_employee_id) REFERENCES employees(id) ON DELETE RESTRICT,
    CONSTRAINT fk_visitors_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_visitors_status (status),
    INDEX idx_visitors_host (host_employee_id),
    INDEX idx_visitors_check_in (check_in_time),
    INDEX idx_visitors_created (created_at)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Visitor Approval Workflow
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS visitor_approvals (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    visitor_id  INT NOT NULL,
    employee_id INT NOT NULL,
    status      ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    comments    TEXT,
    approved_at DATETIME NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_approvals_visitor FOREIGN KEY (visitor_id) REFERENCES visitors(id) ON DELETE CASCADE,
    CONSTRAINT fk_approvals_employee FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE RESTRICT,
    INDEX idx_approvals_visitor (visitor_id),
    INDEX idx_approvals_status (status)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Audit Log
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NULL,
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id   INT,
    details     TEXT,
    ip_address  VARCHAR(45),
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_audit_created (created_at),
    INDEX idx_audit_action (action)
) ENGINE=InnoDB;

-- ============================================================
-- Seed Data
-- ============================================================

INSERT INTO departments (name, description) VALUES
('Human Resources', 'HR and people operations'),
('Information Technology', 'IT infrastructure and software'),
('Finance', 'Financial planning and accounting'),
('Operations', 'Day-to-day business operations'),
('Marketing', 'Marketing and communications');

-- Default users are created by database/seed_users.py after schema import.

INSERT INTO employees (user_id, department_id, employee_code, first_name, last_name, phone, email, designation) VALUES
(NULL, 1, 'EMP001', 'Sarah', 'Johnson', '555-0101', 'sarah.j@vms.local', 'HR Manager'),
(NULL, 2, 'EMP002', 'Michael', 'Chen', '555-0102', 'michael.c@vms.local', 'Senior Developer'),
(NULL, 2, 'EMP003', 'John', 'Doe', '555-0103', 'employee1@vms.local', 'Software Engineer');
