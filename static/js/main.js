// Main JavaScript for AAA Performance Tracker

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Form validation enhancements
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Rating form enhancements
    const ratingForms = document.querySelectorAll('form[method="POST"]');
    ratingForms.forEach(form => {
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn) {
            let isSubmitting = false;
            form.addEventListener('submit', function(e) {
                if (isSubmitting) {
                    e.preventDefault();
                    return false;
                }
                isSubmitting = true;
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
                
                // Re-enable after 5 seconds as a fallback
                setTimeout(() => {
                    isSubmitting = false;
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                }, 5000);
            });
        }
    });

    // Auto-save form data to localStorage (for recovery)
    const formInputs = document.querySelectorAll('textarea, input[type="text"], input[type="email"]');
    formInputs.forEach(input => {
        const storageKey = `aaaperformance_${input.name || input.id}`;
        
        // Load saved data
        const savedValue = localStorage.getItem(storageKey);
        if (savedValue && !input.value) {
            input.value = savedValue;
        }
        
        // Save data on input
        input.addEventListener('input', function() {
            localStorage.setItem(storageKey, input.value);
        });
        
        // Clear saved data on successful form submission
        const form = input.closest('form');
        if (form) {
            form.addEventListener('submit', function() {
                setTimeout(() => {
                    localStorage.removeItem(storageKey);
                }, 1000);
            });
        }
    });

    // Progress bar animations
    const progressBars = document.querySelectorAll('.progress-bar');
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const progressObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const progressBar = entry.target;
                const width = progressBar.style.width;
                progressBar.style.width = '0%';
                setTimeout(() => {
                    progressBar.style.width = width;
                }, 100);
            }
        });
    }, observerOptions);

    progressBars.forEach(bar => {
        progressObserver.observe(bar);
    });

    // Confirmation dialogs for critical actions
    const deleteButtons = document.querySelectorAll('[data-action="delete"]');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Enhanced table sorting functionality
    function initializeTableSorting() {
        const tables = document.querySelectorAll('table.sortable, table.table');
        
        tables.forEach(table => {
            const headers = table.querySelectorAll('thead th');
            
            headers.forEach((header, index) => {
                // Skip action columns and empty headers
                if (header.textContent.trim().toLowerCase().includes('action') || 
                    header.textContent.trim() === '' ||
                    header.classList.contains('no-sort')) {
                    return;
                }
                
                header.style.cursor = 'pointer';
                header.style.userSelect = 'none';
                header.classList.add('sortable-header');
                
                // Add sort indicator
                if (!header.querySelector('.sort-indicator')) {
                    const indicator = document.createElement('span');
                    indicator.className = 'sort-indicator ms-1';
                    indicator.innerHTML = '<i class="fas fa-sort text-muted"></i>';
                    header.appendChild(indicator);
                }
                
                header.addEventListener('click', function() {
                    sortTable(table, index, header);
                });
            });
        });
    }
    
    function sortTable(table, columnIndex, header) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const indicator = header.querySelector('.sort-indicator');
        
        // Determine current sort direction
        let isAscending = true;
        if (header.classList.contains('sort-asc')) {
            isAscending = false;
        }
        
        // Clear all other sort indicators
        table.querySelectorAll('thead th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
            const ind = th.querySelector('.sort-indicator i');
            if (ind) {
                ind.className = 'fas fa-sort text-muted';
            }
        });
        
        // Set current sort indicator
        header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
        indicator.querySelector('i').className = isAscending ? 
            'fas fa-sort-up text-primary' : 'fas fa-sort-down text-primary';
        
        // Sort rows
        rows.sort((a, b) => {
            const cellA = a.cells[columnIndex];
            const cellB = b.cells[columnIndex];
            
            if (!cellA || !cellB) return 0;
            
            let valueA = getCellValue(cellA);
            let valueB = getCellValue(cellB);
            
            // Handle different data types
            const numA = parseFloat(valueA.replace(/[^\d.-]/g, ''));
            const numB = parseFloat(valueB.replace(/[^\d.-]/g, ''));
            
            let result = 0;
            
            // Check if both are numbers
            if (!isNaN(numA) && !isNaN(numB)) {
                result = numA - numB;
            } 
            // Check if both are dates
            else if (isDate(valueA) && isDate(valueB)) {
                const dateA = new Date(valueA);
                const dateB = new Date(valueB);
                result = dateA - dateB;
            }
            // String comparison
            else {
                result = valueA.localeCompare(valueB, undefined, {numeric: true});
            }
            
            return isAscending ? result : -result;
        });
        
        // Reorder rows in DOM
        rows.forEach(row => tbody.appendChild(row));
        
        // Add visual feedback
        tbody.style.opacity = '0.7';
        setTimeout(() => {
            tbody.style.opacity = '1';
        }, 150);
    }
    
    function getCellValue(cell) {
        // Get text content, ignoring badges and icons
        let text = cell.textContent || cell.innerText || '';
        
        // Handle special cases
        const badge = cell.querySelector('.badge');
        if (badge) {
            text = badge.textContent.trim();
        }
        
        return text.trim();
    }
    
    function isDate(str) {
        const datePatterns = [
            /^\d{1,2}\/\d{1,2}\/\d{4}$/,  // MM/DD/YYYY
            /^\d{4}-\d{2}-\d{2}$/,        // YYYY-MM-DD
            /^\w{3}\s+\d{1,2},\s+\d{4}$/  // Month DD, YYYY
        ];
        
        return datePatterns.some(pattern => pattern.test(str.trim()));
    }
    
    // Initialize table sorting when DOM is loaded
    initializeTableSorting();

    // Search functionality for tables
    const searchInputs = document.querySelectorAll('.table-search');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const table = document.querySelector(this.dataset.target);
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    });

    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            // Skip empty anchors
            if (targetId && targetId !== '#') {
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    e.preventDefault();
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Auto-refresh for dashboard pages (every 5 minutes)
    if (window.location.pathname.includes('dashboard')) {
        setInterval(function() {
            // Only refresh if user is active (to save resources)
            if (document.visibilityState === 'visible') {
                location.reload();
            }
        }, 300000); // 5 minutes
    }

    // Enhanced error handling for AJAX requests
    window.handleAjaxError = function(error) {
        console.error('AJAX Error:', error);
        
        // Show user-friendly error message
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            <strong>Error!</strong> Something went wrong. Please refresh the page and try again.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
        }
    };

    // Print functionality for reports
    window.printReport = function() {
        window.print();
    };

    // Export functionality helpers
    window.exportData = function(format, endpoint) {
        const link = document.createElement('a');
        link.href = endpoint;
        link.download = `aaaperformance_export_${new Date().toISOString().split('T')[0]}.${format}`;
        link.click();
    };
});

// Utility functions
window.AAAPerformance = {
    // Format numbers consistently
    formatRating: function(rating) {
        return parseFloat(rating).toFixed(1);
    },
    
    // Generate random colors for charts
    generateColors: function(count) {
        const colors = [];
        for (let i = 0; i < count; i++) {
            const hue = (i * 137.508) % 360; // Golden angle approximation
            colors.push(`hsla(${hue}, 70%, 50%, 0.8)`);
        }
        return colors;
    },
    
    // Debounce function for search inputs
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};
