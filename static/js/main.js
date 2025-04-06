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

/**
 * PWA and Mobile Optimization functionality
 */

// Check for offline status and update UI accordingly
function updateOnlineStatus() {
    const offlineIndicator = document.querySelector('.offline-indicator');
    if (!offlineIndicator) {
        // Create offline indicator if it doesn't exist
        const indicator = document.createElement('div');
        indicator.className = 'offline-indicator';
        indicator.textContent = 'Вы сейчас работаете офлайн';
        document.body.appendChild(indicator);
    }
    
    if (navigator.onLine) {
        document.body.classList.remove('offline');
    } else {
        document.body.classList.add('offline');
    }
}

// Add offline indicator to the document
document.addEventListener('DOMContentLoaded', function() {
    // Create offline banner if it doesn't exist yet
    if (!document.querySelector('.offline-indicator')) {
        const offlineIndicator = document.createElement('div');
        offlineIndicator.className = 'offline-indicator';
        offlineIndicator.textContent = 'Вы сейчас работаете офлайн';
        document.body.appendChild(offlineIndicator);
    }
    
    // Add event listeners for online/offline events
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    
    // Check initial status
    updateOnlineStatus();
    
    // Initialize mobile navigation if on small screens
    initMobileNav();
    
    // Use IntersectionObserver for lazy loading if available
    if ('IntersectionObserver' in window) {
        lazyLoadImages();
    }
});

/**
 * Initialize mobile bottom navigation if on small screens
 */
function initMobileNav() {
    // Only for screens smaller than 768px and if in standalone mode
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    const isSmallScreen = window.innerWidth < 768;
    
    if ((isStandalone || isSmallScreen) && !document.querySelector('.mobile-nav')) {
        // Create the mobile nav container
        const nav = document.createElement('div');
        nav.className = 'mobile-nav d-md-none';
        
        // Only create navigation if user is logged in
        if (document.querySelector('.navbar-nav [href*="dashboard"]')) {
            // Add navigation items
            nav.innerHTML = `
                <a href="/" class="mobile-nav-item">
                    <i class="fas fa-home"></i>
                    <span>Главная</span>
                </a>
                <a href="/dashboard" class="mobile-nav-item">
                    <i class="fas fa-chart-line"></i>
                    <span>Дашборд</span>
                </a>
                <a href="/transactions" class="mobile-nav-item">
                    <i class="fas fa-exchange-alt"></i>
                    <span>Транзакции</span>
                </a>
                <a href="/savings_goals" class="mobile-nav-item">
                    <i class="fas fa-piggy-bank"></i>
                    <span>Цели</span>
                </a>
                <a href="/recommendations" class="mobile-nav-item">
                    <i class="fas fa-lightbulb"></i>
                    <span>Советы</span>
                </a>
            `;
            
            document.body.appendChild(nav);
            
            // Mark current page as active
            const currentPath = window.location.pathname;
            const links = nav.querySelectorAll('a');
            links.forEach(link => {
                if (currentPath.includes(link.getAttribute('href').replace('/', ''))) {
                    link.classList.add('text-primary');
                }
            });
        }
    }
}

/**
 * Lazy load images using Intersection Observer
 */
function lazyLoadImages() {
    const imgObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                const src = img.getAttribute('data-src');
                
                if (src) {
                    img.setAttribute('src', src);
                    img.removeAttribute('data-src');
                    img.classList.remove('lazy-load');
                }
                
                observer.unobserve(img);
            }
        });
    });
    
    // Get all images with data-src attribute
    const lazyImages = document.querySelectorAll('img.lazy-load[data-src]');
    lazyImages.forEach(img => {
        imgObserver.observe(img);
    });
}

/**
 * Add to home screen prompt (for browsers that don't support native install)
 */
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent Chrome 67 and earlier from automatically showing the prompt
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    
    // Show the install button if available
    const installButton = document.getElementById('install-button');
    if (installButton) {
        installButton.classList.remove('d-none');
        
        installButton.addEventListener('click', (e) => {
            // Show the install prompt
            deferredPrompt.prompt();
            
            // Wait for the user to respond to the prompt
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                } else {
                    console.log('User dismissed the install prompt');
                }
                deferredPrompt = null;
                installButton.classList.add('d-none');
            });
        });
    }
});

/**
 * Detect touch capability and optimize accordingly
 */
function detectTouchCapability() {
    const isTouchDevice = ('ontouchstart' in window) || 
                          (navigator.maxTouchPoints > 0) || 
                          (navigator.msMaxTouchPoints > 0);
    
    if (isTouchDevice) {
        document.body.classList.add('touch-device');
        
        // Increase target sizes for touch devices
        document.querySelectorAll('.btn-sm').forEach(btn => {
            btn.classList.remove('btn-sm');
        });
    }
}

// Call touch detection on load
document.addEventListener('DOMContentLoaded', detectTouchCapability);

/**
 * Uses the Vibration API for feedback (if available)
 * @param {number} duration - Vibration duration in ms
 */
function vibrateForFeedback(duration = 50) {
    if ('vibrate' in navigator) {
        navigator.vibrate(duration);
    }
}

// Add vibration feedback to buttons with .btn-vibrate class
document.addEventListener('click', function(e) {
    if (e.target.closest('.btn-vibrate')) {
        vibrateForFeedback();
    }
});
