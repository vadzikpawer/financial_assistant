/**
 * Main JavaScript file for FinAssistant
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap components
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Detect online/offline status
    updateOnlineStatus();
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    
    // Add mobile bottom navigation if needed
    initMobileNav();
    
    // Add ripple effect to buttons
    addRippleEffect();
    
    // Lazy load images
    lazyLoadImages();
    
    // Handle PWA installation
    initPWAInstall();
    
    // Add touch optimizations
    detectTouchCapability();
});

// Enable copy to clipboard functionality
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text)
        .then(() => {
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check"></i> Скопировано';
            
            // Vibrate if available
            vibrateForFeedback();
            
            setTimeout(() => {
                button.innerHTML = originalText;
            }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy text: ', err);
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-times"></i> Ошибка';
            
            setTimeout(() => {
                button.innerHTML = originalText;
            }, 2000);
        });
}

// Format number with thousands separator
function formatNumber(num) {
    return new Intl.NumberFormat('ru-RU').format(num);
}

// Update the online/offline indicator
function updateOnlineStatus() {
    const offlineIndicator = document.querySelector('.offline-indicator');
    
    if (navigator.onLine) {
        document.body.classList.remove('offline-mode');
        if (offlineIndicator) {
            offlineIndicator.style.display = 'none';
        }
    } else {
        document.body.classList.add('offline-mode');
        if (offlineIndicator) {
            offlineIndicator.style.display = 'block';
            offlineIndicator.style.transform = 'translateY(0)';
        }
    }
}

// Initialize mobile bottom navigation if on small screens
function initMobileNav() {
    const bottomNav = document.querySelector('.md-bottom-nav');
    if (bottomNav) {
        const mainContent = document.querySelector('main');
        if (mainContent && window.innerWidth < 768) {
            mainContent.style.paddingBottom = '70px';
        }
    }
}

// Add ripple effect to buttons and other clickable elements
function addRippleEffect() {
    const elements = document.querySelectorAll('.md-btn, .md-app-bar-action, .md-bottom-nav-item, .md-drawer-item, .md-list-item');
    
    elements.forEach(element => {
        element.addEventListener('click', function(e) {
            // Only apply ripple if element doesn't have .ripple-disable class
            if (!element.classList.contains('ripple-disable')) {
                const ripple = document.createElement('span');
                const rect = element.getBoundingClientRect();
                
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.width = ripple.style.height = `${size}px`;
                ripple.style.left = `${x}px`;
                ripple.style.top = `${y}px`;
                ripple.className = 'ripple';
                
                // Remove existing ripples
                const currentRipple = element.querySelector('.ripple');
                if (currentRipple) {
                    currentRipple.remove();
                }
                
                element.appendChild(ripple);
                
                // Remove ripple after animation
                setTimeout(() => {
                    ripple.remove();
                }, 600);
            }
        });
    });
}

// Lazy load images using Intersection Observer
function lazyLoadImages() {
    if ('IntersectionObserver' in window) {
        const imgObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const src = img.getAttribute('data-src');
                    
                    if (src) {
                        img.src = src;
                        img.removeAttribute('data-src');
                    }
                    
                    observer.unobserve(img);
                }
            });
        });
        
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => {
            imgObserver.observe(img);
        });
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => {
            img.src = img.getAttribute('data-src');
            img.removeAttribute('data-src');
        });
    }
}

// Handle PWA installation
let deferredPrompt;

function initPWAInstall() {
    const installButton = document.getElementById('install-button');
    const mobileInstallButton = document.getElementById('install-button-mobile');
    
    window.addEventListener('beforeinstallprompt', (e) => {
        // Prevent the mini-infobar from appearing on mobile
        e.preventDefault();
        // Stash the event so it can be triggered later
        deferredPrompt = e;
        // Update UI to notify the user they can install the PWA
        if (installButton) installButton.classList.remove('d-none');
        if (mobileInstallButton) mobileInstallButton.classList.remove('d-none');
    });
    
    if (installButton) {
        installButton.addEventListener('click', () => {
            if (deferredPrompt) {
                // Show the install prompt
                deferredPrompt.prompt();
                
                // Wait for the user to respond to the prompt
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('User accepted the install prompt');
                        installButton.classList.add('d-none');
                        if (mobileInstallButton) mobileInstallButton.classList.add('d-none');
                    } else {
                        console.log('User dismissed the install prompt');
                    }
                    deferredPrompt = null;
                });
            }
        });
    }
    
    // Hide the install button if already installed
    window.addEventListener('appinstalled', () => {
        console.log('PWA was installed');
        if (installButton) installButton.classList.add('d-none');
        if (mobileInstallButton) mobileInstallButton.classList.add('d-none');
        deferredPrompt = null;
    });
}

// Detect touch capability and optimize accordingly
function detectTouchCapability() {
    const isTouchDevice = ('ontouchstart' in window) ||
                         (navigator.maxTouchPoints > 0) ||
                         (navigator.msMaxTouchPoints > 0);
    
    if (isTouchDevice) {
        document.body.classList.add('touch-device');
        
        // Increase tap target sizes for touch devices
        const smallButtons = document.querySelectorAll('.md-btn-sm');
        smallButtons.forEach(button => {
            button.classList.remove('md-btn-sm');
        });
    }
}

// Use Vibration API for feedback (if available)
function vibrateForFeedback(duration = 50) {
    if ('vibrate' in navigator) {
        navigator.vibrate(duration);
    }
}

// Dynamic color theme based on bank
function setThemeForBank(bankName) {
    let primaryColor = '#428bf9'; // Default
    
    switch(bankName.toLowerCase()) {
        case 'tinkoff':
            primaryColor = '#ffdd2d';
            break;
        case 'sberbank':
        case 'sber':
            primaryColor = '#1a9f29';
            break;
        case 'vtb':
            primaryColor = '#009fdf';
            break;
        case 'alfabank':
        case 'альфа-банк':
            primaryColor = '#ef3124';
            break;
        case 'газпромбанк':
        case 'gazprombank':
            primaryColor = '#0079c2';
            break;
    }
    
    document.documentElement.style.setProperty('--md-primary', primaryColor);
}

// Celebrate achievement with animation and confetti
function celebrateAchievement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('celebrate');
        
        // Remove animation class after it completes
        setTimeout(() => {
            element.classList.remove('celebrate');
        }, 500);
        
        // Vibrate in a celebratory pattern
        if ('vibrate' in navigator) {
            navigator.vibrate([100, 50, 100, 50, 100]);
        }
        
        // TODO: Add confetti effect if library is loaded
    }
}

// Handle adding new amount to savings goal with animation
function updateSavingsAmount(goalId, newAmount) {
    const form = document.getElementById(`updateAmountForm${goalId}`);
    if (!form) return;
    
    // Get the form data
    const formData = new FormData(form);
    const amount = parseFloat(formData.get('amount'));
    
    if (isNaN(amount) || amount <= 0) {
        alert('Пожалуйста, введите корректную сумму');
        return;
    }
    
    // Set loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="loader"></span> Обновление...';
    submitBtn.disabled = true;
    
    // Submit with AJAX
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the progress display with animation
            const progressBar = document.querySelector(`.goal-${goalId} .md-progress-bar`);
            const progressBadge = document.querySelector(`.goal-${goalId} .md-badge`);
            const currentAmountEl = document.querySelector(`.goal-${goalId} .current-amount`);
            
            if (progressBar && progressBadge && currentAmountEl) {
                // Animate progress bar
                progressBar.style.width = `${data.progress_percentage}%`;
                
                // Update badge
                progressBadge.textContent = `${data.progress_percentage}%`;
                
                // Update amount with animation
                const oldAmount = parseFloat(currentAmountEl.getAttribute('data-amount'));
                const newAmountValue = parseFloat(data.current_amount);
                currentAmountEl.setAttribute('data-amount', newAmountValue);
                
                // Animate number change
                animateNumberChange(currentAmountEl, oldAmount, newAmountValue);
                
                // Celebrate if goal achieved
                if (data.is_achieved) {
                    celebrateAchievement(`goalCard${goalId}`);
                    
                    // Change badge class
                    progressBadge.className = 'md-badge md-badge-success';
                }
            }
            
            // Show success message
            const alertHtml = `
                <div class="alert alert-success alert-dismissible fade show md-rounded" role="alert">
                    ${data.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
            form.insertAdjacentHTML('beforebegin', alertHtml);
            
            // Reset form
            form.reset();
        } else {
            // Show error
            const alertHtml = `
                <div class="alert alert-danger alert-dismissible fade show md-rounded" role="alert">
                    ${data.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
            form.insertAdjacentHTML('beforebegin', alertHtml);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Произошла ошибка при обновлении цели');
    })
    .finally(() => {
        // Restore button
        submitBtn.innerHTML = originalBtnText;
        submitBtn.disabled = false;
    });
}

// Animate number change
function animateNumberChange(element, startValue, endValue) {
    const duration = 1000; // ms
    const frameDuration = 1000 / 60; // 60fps
    const totalFrames = Math.round(duration / frameDuration);
    let frame = 0;
    
    const formatter = new Intl.NumberFormat('ru-RU');
    
    const animate = () => {
        frame++;
        const progress = frame / totalFrames;
        const currentValue = startValue + (endValue - startValue) * progress;
        
        element.textContent = formatter.format(Math.floor(currentValue)) + ' ₽';
        
        if (frame < totalFrames) {
            requestAnimationFrame(animate);
        }
    };
    
    requestAnimationFrame(animate);
}
