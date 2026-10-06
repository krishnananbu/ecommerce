from django import forms
from .models import Category, Brand, Order

PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)]

class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
    )
    override = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput
    )

    def __init__(self, *args, max_quantity=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_quantity = max_quantity
        if max_quantity is not None:
            self.fields['quantity'].widget.attrs['max'] = str(max_quantity)

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if self.max_quantity is not None and quantity is not None and quantity > self.max_quantity:
            raise forms.ValidationError(f"Only {self.max_quantity} items are available in stock.")
        return quantity

class ProductFilterForm(forms.Form):
    PRICE_CHOICES = [
        ('', 'All Prices'),
        ('0-50', 'Under $50'),
        ('50-100', '$50 - $100'),
        ('100-200', '$100 - $200'),
        ('200-500', '$200 - $500'),
        ('500+', 'Over $500'),
    ]
    
    SORT_CHOICES = [
        ('', 'Default'),
        ('price', 'Price: Low to High'),
        ('-price', 'Price: High to Low'),
        ('name', 'Name: A to Z'),
        ('-name', 'Name: Z to A'),
        ('-created_at', 'Newest First'),
        ('created_at', 'Oldest First'),
    ]
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search products...'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All',
        widget=forms.RadioSelect(attrs={'class': 'd-none'})
    )
    
    brand = forms.ModelMultipleChoiceField(
        queryset=Brand.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    price_max = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    price_range = forms.ChoiceField(
        choices=PRICE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm',
            'form': 'filter-form',
            'onchange': 'this.form.submit()'
        })
    )
    
    featured_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    available_only = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class CheckoutForm(forms.ModelForm):
    order_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Add any special instructions or notes for your order',
            'rows': 3
        })
    )
    
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 
                 'address', 'city', 'state', 'zip_code', 
                 'shipping_method', 'payment_method', 'order_notes']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Delivery Address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ZIP Code'
            }),
            'shipping_method': forms.Select(attrs={
                'class': 'form-control shipping-method-select'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control payment-method-select'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update choice fields to use the model's choices
        self.fields['shipping_method'].choices = Order.SHIPPING_METHOD
        self.fields['payment_method'].choices = Order.PAYMENT_METHOD
        
        # Add help texts and error messages
        self.fields['shipping_method'].help_text = 'Choose your preferred shipping method'
        self.fields['payment_method'].help_text = 'Select how you would like to pay'
        
        # Make important fields required and add error messages
        required_fields = {
            'first_name': 'Please enter your first name',
            'last_name': 'Please enter your last name',
            'email': 'Please enter a valid email address',
            'phone': 'Please enter your phone number',
            'address': 'Please enter your delivery address',
            'city': 'Please enter your city',
            'state': 'Please enter your state',
            'zip_code': 'Please enter your ZIP code'
        }
        
        for field, error_message in required_fields.items():
            self.fields[field].required = True
            self.fields[field].error_messages = {
                'required': error_message
            }
            
    def clean_address(self):
        address = self.cleaned_data.get('address')
        if not address:
            raise forms.ValidationError('Please enter your delivery address')
        elif len(address.strip()) < 10:
            raise forms.ValidationError('Please enter a complete delivery address with house/flat number and street name')
        return address.strip()
        
    def clean(self):
        cleaned_data = super().clean()
        
        # Required field validation with custom messages
        required_fields = {
            'first_name': 'First name is required',
            'last_name': 'Last name is required',
            'email': 'Email address is required',
            'phone': 'Phone number is required',
            'city': 'City is required',
            'state': 'State is required',
            'zip_code': 'ZIP code is required',
            'shipping_method': 'Please select a shipping method',
            'payment_method': 'Please select a payment method'
        }
        
        for field, message in required_fields.items():
            if not cleaned_data.get(field):
                self.add_error(field, message)
                
        # Validate shipping method
        shipping_method = cleaned_data.get('shipping_method')
        if shipping_method and shipping_method not in dict(Order.SHIPPING_METHOD):
            self.add_error('shipping_method', 'Invalid shipping method selected')
            
        # Validate payment method
        payment_method = cleaned_data.get('payment_method')
        if payment_method and payment_method not in dict(Order.PAYMENT_METHOD):
            self.add_error('payment_method', 'Invalid payment method selected')
        
        # Email validation
        email = cleaned_data.get('email')
        if email:
            if not email.strip():
                self.add_error('email', 'Email cannot be empty')
            elif len(email) > 254:
                self.add_error('email', 'Email is too long')
        
        # Phone validation
        phone = cleaned_data.get('phone')
        if phone:
            phone = ''.join(filter(str.isdigit, phone))
            if len(phone) < 10:
                self.add_error('phone', 'Please enter a valid phone number with at least 10 digits')
        
        # ZIP code validation
        zip_code = cleaned_data.get('zip_code')
        if zip_code:
            if not zip_code.strip():
                self.add_error('zip_code', 'ZIP code cannot be empty')
            elif not zip_code.replace('-', '').isdigit():
                self.add_error('zip_code', 'ZIP code should only contain numbers and hyphens')
        
        # Shipping method validation
        shipping_method = cleaned_data.get('shipping_method')
        if shipping_method and shipping_method not in dict(self.fields['shipping_method'].choices):
            self.add_error('shipping_method', 'Please select a valid shipping method')
        
        # Payment method validation
        payment_method = cleaned_data.get('payment_method')
        if payment_method and payment_method not in dict(self.fields['payment_method'].choices):
            self.add_error('payment_method', 'Please select a valid payment method')
        
        return cleaned_data