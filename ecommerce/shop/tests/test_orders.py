from django.test import TransactionTestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.db import connection
from datetime import date, timedelta
from ..cart import Cart
from shop.models import Product, Category, Brand, Order, OrderItem
from decimal import Decimal
import json

User = get_user_model()

class OrderPlacementTests(TransactionTestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test category and brand
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.brand = Brand.objects.create(
            name='Test Brand',
            slug='test-brand'
        )
        
        # Create test product
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test Description',
            price=Decimal('99.99'),
            stock=10,
            available=True,
            featured=True,
            category=self.category,
            brand=self.brand
        )
        
        # Initialize client and login
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # Clear email outbox
        mail.outbox = []

    def add_to_cart(self, product_id, quantity=1):
        """Helper method to add a product to cart"""
        return self.client.post(
            reverse('shop:cart_add', args=[product_id]),
            {'quantity': quantity, 'override': False}
        )

    def test_add_to_cart(self):
        """Test adding a product to the cart"""
        response = self.add_to_cart(self.product.id)
        self.assertEqual(response.status_code, 302)  # Should redirect
        
        # Check cart contents
        response = self.client.get(reverse('shop:cart_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, '99.99')  # Product price

    def test_empty_cart_checkout(self):
        """Test attempting checkout with empty cart"""
        response = self.client.get(reverse('shop:checkout'))
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertRedirects(response, reverse('shop:product_list'))

    def test_checkout_process(self):
        """Test the complete checkout process"""
        # Add product to cart
        self.add_to_cart(self.product.id, 2)
        
        # Get checkout page
        response = self.client.get(reverse('shop:checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shop/checkout.html')
        
        # Submit checkout form
        checkout_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'zip_code': '12345',
            'payment_method': 'cash_on_delivery',
            'shipping_method': 'standard'
        }
        
        response = self.client.post(reverse('shop:checkout'), checkout_data)
        self.assertEqual(response.status_code, 302)  # Should redirect to confirmation
        
        # Check that order was created
        order = Order.objects.latest('created_at')
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.first_name, 'Test')
        self.assertEqual(order.total_amount, Decimal('225.48'))  # (99.99 * 2) + 5.00 + tax
        
        # Check order items
        order_item = order.items.first()
        self.assertEqual(order_item.product, self.product)
        self.assertEqual(order_item.quantity, 2)
        
        # Check confirmation email
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(order.tracking_number, mail.outbox[0].body)

    def test_order_with_insufficient_stock(self):
        """Test placing an order with insufficient stock"""
        # Set product stock to 1
        self.product.stock = 1
        self.product.save()
        
        # Try to add 2 items to cart
        self.add_to_cart(self.product.id, 2)
        
        # Submit checkout
        checkout_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'zip_code': '12345',
            'payment_method': 'cash_on_delivery',
            'shipping_method': 'standard'
        }
        
        response = self.client.post(reverse('shop:checkout'), checkout_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('shop:cart_detail'))

    def test_order_tracking(self):
        """Test order tracking functionality"""
        # Place an order first
        self.add_to_cart(self.product.id)
        checkout_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'zip_code': '12345',
            'payment_method': 'cash_on_delivery',
            'shipping_method': 'standard'
        }
        self.client.post(reverse('shop:checkout'), checkout_data)
        
        # Get the order
        order = Order.objects.latest('created_at')
        
        # Test tracking with order number
        response = self.client.get(
            reverse('shop:track_order') + f'?order_number={order.tracking_number}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shop/track_order.html')
        self.assertContains(response, order.tracking_number)

    def test_order_totals_calculation(self):
        """Test order totals calculation"""
        self.add_to_cart(self.product.id, 2)
        checkout_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'zip_code': '12345',
            'payment_method': 'cash_on_delivery',
            'shipping_method': 'express'  # Testing with express shipping
        }
        
        self.client.post(reverse('shop:checkout'), checkout_data)
        order = Order.objects.latest('created_at')
        
        # Calculate expected totals
        subtotal = Decimal('199.98')  # 99.99 * 2
        shipping = Decimal('15.00')  # Express shipping
        tax = Decimal('21.50')  # (199.98 + 15.00) * 0.10, rounded to 2 decimal places
        total = Decimal('236.48')  # 199.98 + 15.00 + 21.50
        
        self.assertEqual(order.subtotal, subtotal)
        self.assertEqual(order.shipping_cost, shipping)
        self.assertEqual(order.tax, tax)
        self.assertEqual(order.total_amount, total)

    def test_multiple_items_order(self):
        """Test placing an order with multiple different items"""
        # Create another product
        product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            description='Test Description 2',
            price=Decimal('49.99'),
            stock=5,
            available=True,
            category=self.category,
            brand=self.brand
        )
        
        # Add both products to cart
        self.add_to_cart(self.product.id, 1)
        self.add_to_cart(product2.id, 2)
        
        # Place order
        checkout_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'zip_code': '12345',
            'payment_method': 'cash_on_delivery',
            'shipping_method': 'standard'
        }
        
        response = self.client.post(reverse('shop:checkout'), checkout_data)
        order = Order.objects.latest('created_at')
        
        # Check order items
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(
            sum(item.quantity for item in order.items.all()),
            3  # 1 + 2 items
        )

    def test_order_status_updates(self):
        """Test order status updates"""
        # Place an order
        self.add_to_cart(self.product.id)
        checkout_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'zip_code': '12345',
            'payment_method': 'cash_on_delivery',
            'shipping_method': 'standard'
        }
        
        self.client.post(reverse('shop:checkout'), checkout_data)
        order = Order.objects.latest('created_at')
        
        # Check initial status
        self.assertEqual(order.status, 'confirmed')  # For cash on delivery
        
        # Check status updates in order history
        self.assertTrue(order.status_updates.filter(status='pending').exists())
        self.assertTrue(order.status_updates.filter(status='confirmed').exists())

    def test_estimated_delivery_date(self):
        """Test estimated delivery date calculation"""
        # Test different shipping methods
        shipping_methods = {
            'express': 3,  # 3 days
            'standard': 7,  # 7 days
            'pickup': 1    # 1 day
        }
        
        for method, days in shipping_methods.items():
            # Clear existing orders and add product to cart
            Order.objects.all().delete()
            cart = Cart(self.client)
            cart.clear()
            self.add_to_cart(self.product.id)
            
            checkout_data = {
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com',
                'phone': '1234567890',
                'address': '123 Test St',
                'city': 'Test City',
                'state': 'Test State',
                'zip_code': '12345',
                'payment_method': 'cash_on_delivery',
                'shipping_method': method
            }
            
            response = self.client.post(reverse('shop:checkout'), checkout_data)
            self.assertEqual(response.status_code, 302)  # Successful redirect
            
            try:
                order = Order.objects.latest('created_at')
                today = date.today()
                expected_delivery = today + timedelta(days=days)
                self.assertEqual(order.estimated_delivery, expected_delivery,
                               f"Expected delivery in {days} days for {method} shipping")
            except Order.DoesNotExist:
                self.fail(f"Order was not created for {method} shipping method")