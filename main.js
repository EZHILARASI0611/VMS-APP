/**
 * VMS - Main JavaScript utilities
 */

document.addEventListener('DOMContentLoaded', function () {
    initSidebarToggle();
    initAlerts();
    initConfirmDelete();
    initPhotoPreview();
});

/** Mobile sidebar toggle */
function initSidebarToggle() {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    if (toggle && sidebar) {
        toggle.addEventListener('click', function () {
            sidebar.classList.toggle('show');
        });
    }
}

/** Auto-dismiss flash alerts after 5 seconds */
function initAlerts() {
    document.querySelectorAll('.alert-dismissible').forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });
}

/** Confirm before delete actions */
function initConfirmDelete() {
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (!confirm(el.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    });
}

/** Preview uploaded photo before submit */
function initPhotoPreview() {
    const photoInput = document.getElementById('photo');
    const preview = document.getElementById('photoPreview');
    if (photoInput && preview) {
        photoInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    preview.src = e.target.result;
                    preview.classList.remove('d-none');
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

/** Format status for display */
function formatStatus(status) {
    return status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

/** API helper for authenticated fetch */
async function apiFetch(url, options = {}) {
    const defaults = {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
    };
    const response = await fetch(url, { ...defaults, ...options });
    return response.json();
}

/** Export chart colors */
const CHART_COLORS = {
    primary: '#0d6efd',
    success: '#198754',
    warning: '#ffc107',
    danger: '#dc3545',
    info: '#0dcaf0',
    secondary: '#6c757d',
};
