/**
 * Main JavaScript file for FinAssistant
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        let alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            let bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Password strength meter
    const passwordField = document.getElementById('password');
    const passwordStrength = document.getElementById('password-strength');
    
    if (passwordField && passwordStrength) {
        passwordField.addEventListener('input', function() {
            const password = passwordField.value;
            let strength = 0;
            
            // Length check
            if (password.length >= 8) strength += 1;
            
            // Lowercase check
            if (/[a-z]/.test(password)) strength += 1;
            
            // Uppercase check
            if (/[A-Z]/.test(password)) strength += 1;
            
            // Number check
            if (/[0-9]/.test(password)) strength += 1;
            
            // Special character check
            if (/[^A-Za-z0-9]/.test(password)) strength += 1;
            
            // Update strength meter
            passwordStrength.className = 'progress-bar';
            passwordStrength.style.width = (strength * 20) + '%';
            
            if (strength <= 2) {
                passwordStrength.classList.add('bg-danger');
            } else if (strength <= 3) {
                passwordStrength.classList.add('bg-warning');
            } else {
                passwordStrength.classList.add('bg-success');
            }
        });
    }

    // Format currency inputs
    const currencyInputs = document.querySelectorAll('.currency-input');
    currencyInputs.forEach(function(input) {
        input.addEventListener('blur', function(e) {
            const value = e.target.value.replace(/[^\d]/g, '');
            if (value) {
                e.target.value = new Intl.NumberFormat('ru-RU').format(value);
            }
        });
        
        input.addEventListener('focus', function(e) {
            e.target.value = e.target.value.replace(/[^\d]/g, '');
        });
    });

    // Date range picker (if available)
    const dateFromInput = document.getElementById('date_from');
    const dateToInput = document.getElementById('date_to');
    
    if (dateFromInput && dateToInput) {
        dateFromInput.addEventListener('change', function() {
            dateToInput.min = dateFromInput.value;
        });
        
        dateToInput.addEventListener('change', function() {
            dateFromInput.max = dateToInput.value;
        });
    }

    // Confirmation for delete actions
    const confirmDeleteForms = document.querySelectorAll('.confirm-delete-form');
    
    confirmDeleteForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const confirmed = confirm('Вы уверены, что хотите удалить этот элемент? Это действие невозможно отменить.');
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });
});

/**
 * Format number as currency
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatNumber(num) {
    return new Intl.NumberFormat('ru-RU').format(num);
}

/**
 * Copy to clipboard
 * @param {string} text - Text to copy
 * @param {Element} button - Button element that triggered the copy
 */
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(function() {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i> Скопировано';
        
        setTimeout(function() {
            button.innerHTML = originalText;
        }, 2000);
    }, function() {
        alert('Не удалось скопировать текст');
    });
}
