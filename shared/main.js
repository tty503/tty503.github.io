/* ==================== SHARED UTILITIES ==================== */

(function() {
    'use strict';

    // Auto-fill current year in copyright
    var yearEl = document.getElementById('current-year');
    if (yearEl) {
        yearEl.textContent = new Date().getFullYear();
    }

    // Navbar scroll opacity effect
    var navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                navbar.style.background = 'rgba(3, 3, 3, 0.9)';
            } else {
                navbar.style.background = 'rgba(3, 3, 3, 0.75)';
            }
        });
    }
})();
