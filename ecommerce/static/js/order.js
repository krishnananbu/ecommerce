// Update shipping cost and total when shipping method changes
document.addEventListener('DOMContentLoaded', function() {
    // Form elements
    const form = document.querySelector('form');
    const submitButton = document.getElementById('place-order-btn');
    const spinner = submitButton ? submitButton.querySelector('.spinner-border') : null;
    const shippingSelect = document.querySelector('.shipping-method-select');
    const paymentSelect = document.querySelector('.payment-method-select');

    // Form validation functions
    function validateEmail(email) {
        const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    }

    function validatePhone(phone) {
        return phone.replace(/\D/g, '').length >= 10;
    }

    function validateZipCode(zipCode) {
        return /^\d{5}(-\d{4})?$/.test(zipCode);
    }
    
    function validateAddress(address) {
        if (!address) return false;
        address = address.trim();
        if (address.length < 10) return false;
        // Check for house/flat number
        if (!/\d/.test(address)) return false;
        return true;
    }

    // Update shipping cost based on selected method
    function updateShippingCost(method) {
        let shippingCost = 5.00;
        if (method === 'standard') {
            shippingCost = 5.00;
        } else if (method === 'express') {
            shippingCost = 15.00;
        } else if (method === 'pickup') {
            shippingCost = 0.00;
        }

        // Update shipping cost display
        const shippingElement = document.getElementById('shipping-cost');
        if (shippingElement) {
            shippingElement.textContent = shippingCost === 0 ? 'Free' : `$${shippingCost.toFixed(2)}`;
        }

        // Update total
        updateTotal(shippingCost);
    }

    // Update total amount including 10% tax
    function updateTotal(shippingCost) {
        const subtotalElement = document.getElementById('subtotal');
        const taxElement = document.getElementById('tax-amount');
        const totalElement = document.getElementById('total-amount');
        
        if (subtotalElement && totalElement) {
            const subtotal = parseFloat(subtotalElement.getAttribute('data-value')) || 0;
            const taxableAmount = subtotal + shippingCost;
            const tax = taxableAmount * 0.10;
            const total = taxableAmount + tax;
            
            if (taxElement) {
                taxElement.textContent = `$${tax.toFixed(2)}`;
            }
            totalElement.textContent = `$${total.toFixed(2)}`;
        }
    }

    // Handle payment method selection
    function updatePaymentMethod(method) {
        const paymentFields = document.querySelectorAll('.payment-fields');
        paymentFields.forEach(field => {
            field.style.display = 'none';
        });

        const selectedField = document.getElementById(`${method}-fields`);
        if (selectedField) {
            selectedField.style.display = 'block';
        }
    }

    // Set up event listeners and form handling
    if (shippingSelect) {
        shippingSelect.addEventListener('change', function() {
            updateShippingCost(this.value);
        });
        // Set initial shipping cost
        updateShippingCost(shippingSelect.value);
    }

    if (paymentSelect) {
        paymentSelect.addEventListener('change', function() {
            updatePaymentMethod(this.value);
        });
        // Show initial payment method fields  
        updatePaymentMethod(paymentSelect.value);
    }

    if (form) {
        // Set initial shipping cost if not already set
        if (!shippingSelect) {
            updateShippingCost('standard');
        }
        
        // Real-time field validation
        const emailInput = form.querySelector('input[name="email"]');
        const phoneInput = form.querySelector('input[name="phone"]');
        const zipInput = form.querySelector('input[name="zip_code"]');
        const addressInput = form.querySelector('input[name="address"]');
        
        if (emailInput) {
            emailInput.addEventListener('blur', function() {
                if (!validateEmail(this.value)) {
                    this.classList.add('is-invalid');
                    this.nextElementSibling?.remove();
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'Please enter a valid email address';
                    this.parentNode.appendChild(feedback);
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                    this.nextElementSibling?.remove();
                }
            });
        }

        if (phoneInput) {
            phoneInput.addEventListener('blur', function() {
                if (!validatePhone(this.value)) {
                    this.classList.add('is-invalid');
                    this.nextElementSibling?.remove();
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'Please enter a valid phone number (at least 10 digits)';
                    this.parentNode.appendChild(feedback);
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                    this.nextElementSibling?.remove();
                }
            });
        }

        if (zipInput) {
            zipInput.addEventListener('blur', function() {
                if (!validateZipCode(this.value)) {
                    this.classList.add('is-invalid');
                    this.nextElementSibling?.remove();
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'Please enter a valid ZIP code (e.g., 12345 or 12345-6789)';
                    this.parentNode.appendChild(feedback);
                } else {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                    this.nextElementSibling?.remove();
                }
            });

            if (addressInput) {
                addressInput.addEventListener('blur', function() {
                    const alertDiv = this.parentNode.querySelector('.alert-danger');
                    if (alertDiv) alertDiv.remove();
                    
                    if (!this.value.trim()) {
                        this.classList.add('is-invalid');
                        const feedback = document.createElement('div');
                        feedback.className = 'alert alert-danger mt-2';
                        feedback.innerHTML = '<i class="fas fa-exclamation-circle"></i> Please enter your delivery address';
                        this.parentNode.appendChild(feedback);
                    } else if (!validateAddress(this.value)) {
                        this.classList.add('is-invalid');
                        const feedback = document.createElement('div');
                        feedback.className = 'alert alert-danger mt-2';
                        feedback.innerHTML = 
                            '<div><i class="fas fa-exclamation-circle"></i> Please provide a complete address including:</div>' +
                            '<ul class="mb-0 mt-1">' +
                            '<li>House/flat number</li>' +
                            '<li>Street name</li>' +
                            '<li>Area/locality</li>' +
                            '</ul>';
                        this.parentNode.appendChild(feedback);
                    } else {
                        this.classList.remove('is-invalid');
                        this.classList.add('is-valid');
                    }
                });
            }
        }
        
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Reset previous error messages
            const existingAlerts = form.querySelectorAll('.alert');
            existingAlerts.forEach(alert => alert.remove());
            
            // Custom validation
            let isValid = true;
            const requiredFields = [
                'first_name', 'last_name', 'email', 'phone',
                'address', 'city', 'state', 'zip_code',
                'shipping_method', 'payment_method'
            ];
            
            requiredFields.forEach(field => {
                const input = form.querySelector(`[name="${field}"]`);
                if (input && !input.value.trim()) {
                    input.classList.add('is-invalid');
                    isValid = false;
                }
            });
            
            // Additional field validation
            const email = form.querySelector('[name="email"]');
            if (email && !validateEmail(email.value)) {
                email.classList.add('is-invalid');
                isValid = false;
            }
            
            const phone = form.querySelector('[name="phone"]');
            if (phone && !validatePhone(phone.value)) {
                phone.classList.add('is-invalid');
                isValid = false;
            }
            
            const zip = form.querySelector('[name="zip_code"]');
            if (zip && !validateZipCode(zip.value)) {
                zip.classList.add('is-invalid');
                isValid = false;
            }
            
            if (!isValid) {
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-danger';
                alertDiv.textContent = 'Please fix the errors in the form before submitting.';
                form.insertBefore(alertDiv, form.firstChild);
                return;
            }
            
            // Disable submit button and show spinner
            if (submitButton) {
                const btnText = submitButton.querySelector('.btn-text');
                submitButton.disabled = true;
                if (spinner) spinner.classList.remove('d-none');
                if (btnText) btnText.textContent = 'Processing Order...';
            }
            
            // Submit form after a short delay to allow UI updates
            setTimeout(() => {
                try {
                    form.submit();
                } catch (err) {
                    console.error('Form submission error:', err);
                    if (submitButton) {
                        submitButton.disabled = false;
                        if (spinner) spinner.classList.add('d-none');
                        const btnText = submitButton.querySelector('.btn-text');
                        if (btnText) btnText.textContent = 'Place Order';
                    }
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-danger';
                    alertDiv.textContent = 'An error occurred while submitting your order. Please try again.';
                    form.insertBefore(alertDiv, form.firstChild);
                }
            }, 100);
        });
    }
});

// Update order status in real-time (for order detail page)
function updateOrderStatus(orderId, status) {
    fetch(`/shop/api/orders/${orderId}/status/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ status: status })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update status badge
            const statusBadge = document.querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.textContent = status;
                const statusClasses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled'];
                statusClasses.forEach(cls => statusBadge.classList.remove(`status-${cls}`));
                statusBadge.classList.add(`status-${status.toLowerCase()}`);
            }
            
            // Add status update to timeline
            const timeline = document.querySelector('.timeline');
            if (timeline) {
                const newStatus = document.createElement('div');
                newStatus.className = 'timeline-item';
                newStatus.innerHTML = `
                    <div class="timeline-date">${new Date().toLocaleString()}</div>
                    <div class="timeline-content">
                        <h6>${status}</h6>
                        <p>Order status updated to ${status}</p>
                    </div>
                `;
                timeline.insertBefore(newStatus, timeline.firstChild);

                // Show success message
                const alertContainer = document.querySelector('.alert-container');
                if (alertContainer) {
                    const alert = document.createElement('div');
                    alert.className = 'alert alert-success alert-dismissible fade show';
                    alert.innerHTML = `
                        Order status successfully updated to <strong>${status}</strong>
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;
                    alertContainer.appendChild(alert);

                    // Auto-dismiss after 5 seconds
                    setTimeout(() => {
                        alert.classList.remove('show');
                        setTimeout(() => alert.remove(), 150);
                    }, 5000);
                }
            }
        }
    })
    .catch(error => {
        console.error('Error updating order status:', error);
        // Show error message
        const alertContainer = document.querySelector('.alert-container');
        if (alertContainer) {
            const alert = document.createElement('div');
            alert.className = 'alert alert-danger alert-dismissible fade show';
            alert.innerHTML = `
                Failed to update order status. Please try again.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            alertContainer.appendChild(alert);

            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }, 5000);
        }
    });
}

// Initialize status update buttons
document.addEventListener('DOMContentLoaded', function() {
    const statusButtons = document.querySelectorAll('[data-order-status]');
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const orderId = this.getAttribute('data-order-id');
            const newStatus = this.getAttribute('data-order-status');
            if (orderId && newStatus) {
                updateOrderStatus(orderId, newStatus);
            }
        });
    });
});

// Utility function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}