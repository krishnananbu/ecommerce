document.addEventListener('DOMContentLoaded', function() {
    // 1. Price Range Slider
    const priceRange = document.getElementById('priceRange');
    const priceMaxHidden = document.getElementById('price_max_hidden');
    if (priceRange && priceMaxHidden) {
        priceRange.addEventListener('change', function() {
            priceMaxHidden.value = this.value;
        });
    }

    // 2. Sticky Mobile Add to Cart
    const stickyCart = document.getElementById('stickyCart');
    const mainAddToCart = document.querySelector('.product-add-to-cart-form');
    if (stickyCart && mainAddToCart) {
        window.addEventListener('scroll', function() {
            const rect = mainAddToCart.getBoundingClientRect();
            if (rect.bottom < 0) {
                stickyCart.classList.add('show');
            } else {
                stickyCart.classList.remove('show');
            }
        });
    }

    // 3. Form Validation (Real-time)
    const checkoutForm = document.querySelector('.needs-validation');
    if (checkoutForm) {
        const inputs = checkoutForm.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid') || this.classList.contains('is-valid')) {
                    validateField(this);
                }
            });
        });
    }

    function validateField(field) {
        if (field.hasAttribute('required') && !field.value.trim()) {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
        } else if (field.type === 'email' && field.value && !isValidEmail(field.value)) {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
        } else if (field.name === 'phone' && field.value && !isValidPhone(field.value)) {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
        } else if (field.value.trim()) {
            field.classList.add('is-valid');
            field.classList.remove('is-invalid');
        }
    }

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function isValidPhone(phone) {
        return /^\+?[\d\s-]{10,}$/.test(phone);
    }
});
